from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.prescription import Prescription
from services.prescription_service import save_image_to_disk, overwrite_image_on_disk


async def save_prescription(session_id: str, patient_id: str, image_data: str, db: AsyncSession):
    try:
        filepath, prescription_id = save_image_to_disk(image_data)
        record = Prescription(
            id=prescription_id,
            session_id=session_id,
            patient_id=patient_id,
            image_path=filepath,
            created_at=datetime.utcnow()
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return {"status": "success", "data": {"prescription_id": prescription_id, "image_path": filepath}, "message": "Prescription saved"}
    except Exception as e:
        await db.rollback()
        return {"status": "error", "data": None, "message": str(e)}


async def get_prescription(prescription_id: str, db: AsyncSession):
    try:
        result = await db.execute(select(Prescription).where(Prescription.id == prescription_id))
        row = result.scalar_one_or_none()
        if not row:
            return {"status": "error", "data": None, "message": "Not found"}
        return {"status": "success", "data": {"prescription_id": row.id, "session_id": row.session_id, "patient_id": row.patient_id, "image_path": row.image_path}, "message": "Fetched"}
    except Exception as e:
        return {"status": "error", "data": None, "message": str(e)}


async def get_prescriptions_by_session(session_id: str, db: AsyncSession):
    try:
        result = await db.execute(select(Prescription).where(Prescription.session_id == session_id))
        rows = result.scalars().all()
        return {"status": "success", "data": {"prescriptions": [{"id": r.id, "image_path": r.image_path} for r in rows]}, "message": f"{len(rows)} found"}
    except Exception as e:
        return {"status": "error", "data": None, "message": str(e)}


async def update_prescription(prescription_id: str, image_data: str, db: AsyncSession):
    try:
        result = await db.execute(select(Prescription).where(Prescription.id == prescription_id))
        row = result.scalar_one_or_none()
        if not row:
            return {"status": "error", "data": None, "message": "Not found"}
        overwrite_image_on_disk(row.image_path, image_data)
        row.created_at = datetime.utcnow()
        await db.commit()
        return {"status": "success", "data": {"prescription_id": prescription_id}, "message": "Updated"}
    except Exception as e:
        await db.rollback()
        return {"status": "error", "data": None, "message": str(e)}
