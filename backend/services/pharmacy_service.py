from datetime import date, datetime, time

from fastapi import HTTPException
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.consultation import Consultation
from models.patient import Patient
from models.pharmacy import Pharmacy
from models.prescription import Prescription


ACTIVE_STATUSES = ("pending", "preparing", "ready")
STATUS_TRANSITIONS = {
    "pending": "preparing",
    "preparing": "ready",
    "ready": "collected",
}


async def assign_pharmacy(db: AsyncSession) -> int:
    """Return the available pharmacy id with the fewest active prescriptions."""
    active_count = func.coalesce(
        func.sum(case((Prescription.status.in_(ACTIVE_STATUSES), 1), else_=0)),
        0,
    ).label("active_count")

    stmt = (
        select(Pharmacy.id, active_count)
        .outerjoin(Prescription, Prescription.pharmacy_id == Pharmacy.id)
        .where(Pharmacy.is_available.is_(True))
        .group_by(Pharmacy.id)
        .order_by(active_count.asc(), Pharmacy.id.asc())
        .limit(1)
    )

    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        raise HTTPException(status_code=400, detail="No available pharmacies found")

    return row[0]


async def advance_status(
    db: AsyncSession,
    prescription_id: int,
    requested_status: str,
) -> Prescription:
    """Advance a prescription status by one valid step and return the updated row."""
    result = await db.execute(select(Prescription).where(Prescription.id == prescription_id))
    prescription = result.scalar_one_or_none()

    if prescription is None:
        raise HTTPException(status_code=404, detail="Prescription not found")

    current_status = prescription.status
    allowed_next_status = STATUS_TRANSITIONS.get(current_status)

    if allowed_next_status is None or requested_status != allowed_next_status:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition: {current_status} -> {requested_status}",
        )

    prescription.status = requested_status
    await db.commit()
    await db.refresh(prescription)

    return prescription


async def get_queue_items(
    db: AsyncSession,
    pharmacy_id: int,
    statuses: list[str],
):
    """Return queue rows for a pharmacy ordered FIFO with patient details."""
    stmt = (
        select(
            Prescription.id,
            Prescription.status,
            Prescription.created_at,
            Patient.name.label("patient_name"),
            Patient.phone.label("patient_phone"),
            Prescription.consultation_id,
            Prescription.image_mime_type,
        )
        .join(Consultation, Consultation.id == Prescription.consultation_id)
        .join(Patient, Patient.id == Consultation.patient_id)
        .where(Prescription.pharmacy_id == pharmacy_id)
        .where(Prescription.status.in_(statuses))
        .order_by(Prescription.created_at.asc())
    )

    result = await db.execute(stmt)
    return result.mappings().all()


async def get_prescription_image_payload(
    db: AsyncSession,
    prescription_id: int,
) -> tuple[bytes, str]:
    """Fetch a prescription image payload and MIME type."""
    stmt = select(Prescription.image_data, Prescription.image_mime_type).where(
        Prescription.id == prescription_id
    )
    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        raise HTTPException(status_code=404, detail="Prescription not found")

    image_data, image_mime_type = row
    if image_data is None:
        raise HTTPException(status_code=404, detail="No image available")

    return image_data, image_mime_type


async def get_pharmacy_stats(db: AsyncSession, pharmacy_id: int):
    """Aggregate prescription status counts for a pharmacy dashboard."""
    start_of_today = datetime.combine(date.today(), time.min)
    updated_or_created_column = getattr(Prescription, "updated_at", Prescription.created_at)

    stmt = select(
        func.coalesce(func.sum(case((Prescription.status == "pending", 1), else_=0)), 0).label(
            "pending"
        ),
        func.coalesce(func.sum(case((Prescription.status == "preparing", 1), else_=0)), 0).label(
            "preparing"
        ),
        func.coalesce(func.sum(case((Prescription.status == "ready", 1), else_=0)), 0).label(
            "ready"
        ),
        func.coalesce(
            func.sum(
                case(
                    (
                        and_(
                            Prescription.status == "collected",
                            updated_or_created_column >= start_of_today,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("collected_today"),
    ).where(Prescription.pharmacy_id == pharmacy_id)

    result = await db.execute(stmt)
    return result.mappings().one()