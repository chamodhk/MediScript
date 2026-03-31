import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import Base
from models.consultation import Consultation
from models.enums import ConsultationStatus, UserRole
from models.patient import Patient
from models.pharmacy import Pharmacy
from models.prescription import Prescription
from models.user import User
from routers.pharmacy_router import get_prescription_image
from services.pharmacy_service import (
    advance_status,
    assign_pharmacy,
    get_pharmacy_stats,
    get_prescription_image_payload,
    get_queue_items,
)


class PharmacyProcessTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.db = self.session_factory()
        self.doctor = User(
            email="doctor@test.com",
            password_hash="hash",
            full_name="Doctor Test",
            role=UserRole.DOCTOR,
            is_active=True,
        )
        self.pharmacist = User(
            email="pharmacy@test.com",
            password_hash="hash",
            full_name="Pharmacist Test",
            role=UserRole.PHARMACIST,
            is_active=True,
        )
        self.db.add_all(
            [
                Pharmacy(id=1, name="Pharmacy 1", is_available=True),
                Pharmacy(id=2, name="Pharmacy 2", is_available=True),
                self.doctor,
                self.pharmacist,
            ]
        )
        await self.db.commit()
        await self.db.refresh(self.doctor)

    async def asyncTearDown(self) -> None:
        await self.db.close()
        await self.engine.dispose()

    async def _create_patient_consultation_and_prescription(
        self,
        *,
        patient_name: str,
        phone: str,
        token: str,
        pharmacy_id: int,
        status: str,
        created_at: datetime | None = None,
        image_data: bytes | None = b"png-bytes",
        image_mime_type: str = "image/png",
    ) -> Prescription:
        patient = Patient(
            name=patient_name,
            phone=phone,
            preferred_language="en",
            token=token,
        )
        self.db.add(patient)
        await self.db.flush()

        consultation = Consultation(
            patient_id=patient.id,
            doctor_id=self.doctor.id,
            status=ConsultationStatus.IN_PROGRESS,
        )
        self.db.add(consultation)
        await self.db.flush()

        prescription = Prescription(
            consultation_id=consultation.id,
            pharmacy_id=pharmacy_id,
            status=status,
            image_data=image_data,
            image_mime_type=image_mime_type,
            created_at=created_at or datetime.now(),
        )
        self.db.add(prescription)
        await self.db.commit()
        await self.db.refresh(prescription)
        return prescription

    async def test_assign_pharmacy_picks_fewest_active(self) -> None:
        await self._create_patient_consultation_and_prescription(
            patient_name="Patient A",
            phone="0700000001",
            token="T901",
            pharmacy_id=1,
            status="pending",
        )
        await self._create_patient_consultation_and_prescription(
            patient_name="Patient B",
            phone="0700000002",
            token="T902",
            pharmacy_id=1,
            status="ready",
        )
        await self._create_patient_consultation_and_prescription(
            patient_name="Patient C",
            phone="0700000003",
            token="T903",
            pharmacy_id=2,
            status="pending",
        )

        selected_pharmacy_id = await assign_pharmacy(self.db)
        self.assertEqual(selected_pharmacy_id, 2)

    async def test_assign_pharmacy_tie_breaks_with_lowest_id(self) -> None:
        await self._create_patient_consultation_and_prescription(
            patient_name="Patient A",
            phone="0700000011",
            token="T911",
            pharmacy_id=1,
            status="pending",
        )
        await self._create_patient_consultation_and_prescription(
            patient_name="Patient B",
            phone="0700000012",
            token="T912",
            pharmacy_id=2,
            status="ready",
        )

        selected_pharmacy_id = await assign_pharmacy(self.db)
        self.assertEqual(selected_pharmacy_id, 1)

    async def test_assign_pharmacy_raises_when_no_available_pharmacy(self) -> None:
        pharmacy_1 = await self.db.get(Pharmacy, 1)
        pharmacy_2 = await self.db.get(Pharmacy, 2)
        pharmacy_1.is_available = False
        pharmacy_2.is_available = False
        await self.db.commit()

        with self.assertRaises(HTTPException) as ctx:
            await assign_pharmacy(self.db)

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_advance_status_allows_only_next_step(self) -> None:
        prescription = await self._create_patient_consultation_and_prescription(
            patient_name="Patient D",
            phone="0700000021",
            token="T921",
            pharmacy_id=1,
            status="pending",
        )

        updated = await advance_status(self.db, prescription.id, "preparing")
        self.assertEqual(updated.status, "preparing")

        with self.assertRaises(HTTPException) as ctx:
            await advance_status(self.db, prescription.id, "collected")

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_get_queue_items_returns_fifo_with_patient_fields(self) -> None:
        older = datetime.now() - timedelta(minutes=10)
        newer = datetime.now() - timedelta(minutes=1)

        old_item = await self._create_patient_consultation_and_prescription(
            patient_name="Old Patient",
            phone="0700000031",
            token="T931",
            pharmacy_id=1,
            status="pending",
            created_at=older,
        )
        new_item = await self._create_patient_consultation_and_prescription(
            patient_name="New Patient",
            phone="0700000032",
            token="T932",
            pharmacy_id=1,
            status="ready",
            created_at=newer,
        )

        rows = await get_queue_items(self.db, pharmacy_id=1, statuses=["pending", "ready"])

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], old_item.id)
        self.assertEqual(rows[1]["id"], new_item.id)
        self.assertIn("patient_name", rows[0])
        self.assertIn("patient_phone", rows[0])
        self.assertNotIn("image_data", rows[0])

    async def test_get_prescription_image_payload_raises_for_missing_image(self) -> None:
        prescription = await self._create_patient_consultation_and_prescription(
            patient_name="No Image",
            phone="0700000041",
            token="T941",
            pharmacy_id=1,
            status="pending",
            image_data=None,
        )

        with self.assertRaises(HTTPException) as ctx:
            await get_prescription_image_payload(self.db, prescription.id)

        self.assertEqual(ctx.exception.status_code, 404)

    async def test_router_image_endpoint_returns_404_json_for_missing_image(self) -> None:
        prescription = await self._create_patient_consultation_and_prescription(
            patient_name="No Image Router",
            phone="0700000051",
            token="T951",
            pharmacy_id=1,
            status="pending",
            image_data=b"",
        )

        response = await get_prescription_image(
            prescription_id=prescription.id,
            db=self.db,
            _=self.pharmacist,
        )

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.body,
            b'{"detail":"No image available for this prescription"}',
        )

    async def test_router_image_endpoint_returns_streaming_response(self) -> None:
        prescription = await self._create_patient_consultation_and_prescription(
            patient_name="Has Image",
            phone="0700000061",
            token="T961",
            pharmacy_id=1,
            status="pending",
            image_data=b"abc",
            image_mime_type="image/png",
        )

        response = await get_prescription_image(
            prescription_id=prescription.id,
            db=self.db,
            _=self.pharmacist,
        )

        self.assertIsInstance(response, StreamingResponse)
        self.assertEqual(response.media_type, "image/png")

    async def test_router_image_endpoint_returns_500_on_database_error(self) -> None:
        class BrokenSession:
            async def execute(self, _stmt):
                raise SQLAlchemyError("database unavailable")

        response = await get_prescription_image(
            prescription_id=123,
            db=BrokenSession(),
            _=self.pharmacist,
        )

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, 500)

    async def test_get_pharmacy_stats_counts_and_collected_today(self) -> None:
        today_noon = datetime.combine(date.today(), time(hour=12, minute=0))
        yesterday_noon = today_noon - timedelta(days=1)

        await self._create_patient_consultation_and_prescription(
            patient_name="Pending P",
            phone="0700000071",
            token="T971",
            pharmacy_id=1,
            status="pending",
            created_at=today_noon,
        )
        await self._create_patient_consultation_and_prescription(
            patient_name="Preparing P",
            phone="0700000072",
            token="T972",
            pharmacy_id=1,
            status="preparing",
            created_at=today_noon,
        )
        await self._create_patient_consultation_and_prescription(
            patient_name="Ready P",
            phone="0700000073",
            token="T973",
            pharmacy_id=1,
            status="ready",
            created_at=today_noon,
        )
        await self._create_patient_consultation_and_prescription(
            patient_name="Collected Today",
            phone="0700000074",
            token="T974",
            pharmacy_id=1,
            status="collected",
            created_at=today_noon,
        )
        await self._create_patient_consultation_and_prescription(
            patient_name="Collected Old",
            phone="0700000075",
            token="T975",
            pharmacy_id=1,
            status="collected",
            created_at=yesterday_noon,
        )

        counts = await get_pharmacy_stats(self.db, pharmacy_id=1)

        self.assertEqual(int(counts["pending"]), 1)
        self.assertEqual(int(counts["preparing"]), 1)
        self.assertEqual(int(counts["ready"]), 1)
        self.assertEqual(int(counts["collected_today"]), 1)


if __name__ == "__main__":
    unittest.main()
