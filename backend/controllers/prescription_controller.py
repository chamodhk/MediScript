from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.prescription import Prescription
async def save_prescription(consultation_id, pharmacy_id, image_data, image_mime_type, db: AsyncSession):
    try:
        record = Prescription(
            consultation_id=consultation_id,
            pharmacy_id=pharmacy_id,
            image_data=image_data.encode() if image_data else None,
            image_mime_type=image_mime_type or "image/png",
            status="pending"
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record
    except Exception as e:
        await db.rollback()
        raise e

async def get_prescription(prescription_id: int, db: AsyncSession):
    result = await db.execute(select(Prescription).where(Prescription.id == prescription_id))
    return result.scalar_one_or_none()

async def get_prescriptions_by_session(consultation_id: int, db: AsyncSession):
    result = await db.execute(
        select(Prescription).where(Prescription.consultation_id == consultation_id)
        .order_by(Prescription.created_at.desc())
    )
    return result.scalars().all()

async def update_prescription(prescription_id: int, image_data, status, db: AsyncSession):
    try:
        result = await db.execute(select(Prescription).where(Prescription.id == prescription_id))
        row = result.scalar_one_or_none()
        if not row:
            return None
        if image_data:
            row.image_data = image_data.encode()
        if status:
            row.status = status
        await db.commit()
        await db.refresh(row)
        return row
    except Exception as e:
        await db.rollback()
        raise e