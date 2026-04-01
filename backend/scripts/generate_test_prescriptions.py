"""
Generate test prescriptions with time gaps to validate auto pharmacy assignment
and frontend polling behavior.

Run from backend/ directory:
    python scripts/generate_test_prescriptions.py --count 10 --gap 3
"""

import argparse
import asyncio
import base64
import sys
from collections import Counter
from pathlib import Path

# Allow running this file directly via: python scripts/generate_test_prescriptions.py
PROJECT_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_BACKEND_ROOT))

from sqlalchemy import func, select

from core.database import AsyncSessionLocal
from models.consultation import Consultation
from models.enums import UserRole
from models.patient import Patient
from models.prescription import Prescription
from models.user import User
from services.pharmacy_service import assign_pharmacy

PLACEHOLDER_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)
PLACEHOLDER_PNG_BYTES = base64.b64decode(PLACEHOLDER_PNG_BASE64)


async def _resolve_doctor(session, doctor_email: str | None) -> User:
    if doctor_email:
        doctor_result = await session.execute(select(User).where(User.email == doctor_email))
        doctor = doctor_result.scalar_one_or_none()
        if doctor is None:
            raise RuntimeError(f"Doctor not found for email: {doctor_email}")
        return doctor

    first_doctor_result = await session.execute(
        select(User).where(User.role == UserRole.DOCTOR).order_by(User.id.asc())
    )
    first_doctor = first_doctor_result.scalars().first()
    if first_doctor is None:
        raise RuntimeError("No doctor user found. Seed users first.")
    return first_doctor


async def _load_patients(session) -> list[Patient]:
    patients_result = await session.execute(select(Patient).order_by(Patient.id.asc()))
    patients = patients_result.scalars().all()
    if not patients:
        raise RuntimeError("No patients found. Seed patients first.")
    return patients


async def generate_prescriptions(count: int, gap_seconds: float, doctor_email: str | None) -> None:
    assignment_counter: Counter[int] = Counter()

    async with AsyncSessionLocal() as session:
        doctor = await _resolve_doctor(session, doctor_email)
        patients = await _load_patients(session)

        print(f"Using doctor: {doctor.email} (id={doctor.id})")
        print(f"Loaded {len(patients)} patients")

        for index in range(count):
            patient = patients[index % len(patients)]
            pharmacy_id = await assign_pharmacy(session)

            consultation = Consultation(
                patient_id=patient.id,
                doctor_id=doctor.id,
            )
            session.add(consultation)
            await session.flush()

            session.add(
                Prescription(
                    consultation_id=consultation.id,
                    pharmacy_id=pharmacy_id,
                    status="pending",
                    image_data=PLACEHOLDER_PNG_BYTES,
                    image_mime_type="image/png",
                )
            )

            await session.commit()
            assignment_counter[pharmacy_id] += 1

            print(
                f"[{index + 1}/{count}] created consultation_id={consultation.id} "
                f"patient_id={patient.id} -> pharmacy_id={pharmacy_id}"
            )

            if index < count - 1 and gap_seconds > 0:
                await asyncio.sleep(gap_seconds)

        stats_result = await session.execute(
            select(Prescription.pharmacy_id, Prescription.status, func.count(Prescription.id))
            .group_by(Prescription.pharmacy_id, Prescription.status)
            .order_by(Prescription.pharmacy_id.asc(), Prescription.status.asc())
        )

        print("\nAssignment summary for this run:")
        for pharmacy_id, assigned_count in sorted(assignment_counter.items()):
            print(f"- Pharmacy {pharmacy_id}: {assigned_count} new prescriptions")

        print("\nCurrent DB counts by pharmacy/status:")
        for pharmacy_id, status, total in stats_result.all():
            print(f"- pharmacy_id={pharmacy_id} status={status} total={total}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate delayed test prescriptions")
    parser.add_argument("--count", type=int, default=10, help="Number of prescriptions to generate")
    parser.add_argument("--gap", type=float, default=3.0, help="Seconds to wait between each creation")
    parser.add_argument(
        "--doctor-email",
        type=str,
        default="doctor1@mediscript.com",
        help="Doctor email to use for generated consultations",
    )
    args = parser.parse_args()

    if args.count <= 0:
        raise ValueError("--count must be greater than 0")
    if args.gap < 0:
        raise ValueError("--gap must be >= 0")

    await generate_prescriptions(
        count=args.count,
        gap_seconds=args.gap,
        doctor_email=args.doctor_email,
    )


if __name__ == "__main__":
    asyncio.run(main())
