from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.prescription import Prescription
from services.prescription_service import save_image_to_disk, overwrite_image_on_disk


# ─────────────────────────────────────────
# CREATE
# Called by: POST /api/prescription
# Triggered by: "Save & Return" button on canvas page
# ─────────────────────────────────────────

async def save_prescription(
    session_id: str,
    patient_id: str,
    image_data: str,
    db: AsyncSession
):
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

        return {
            "status": "success",
            "data": {
                "prescription_id": prescription_id,
                "session_id": session_id,
                "patient_id": patient_id,
                "image_path": filepath,
                "created_at": record.created_at.isoformat()
            },
            "message": "Prescription saved successfully"
        }

    except Exception as e:
        await db.rollback()
        return {"status": "error", "data": None, "message": str(e)}


# ─────────────────────────────────────────
# READ ONE
# Called by: GET /api/prescription/{id}
# Triggered by: Person A (pharmacy) fetching one prescription
# ─────────────────────────────────────────

async def get_prescription(prescription_id: str, db: AsyncSession):
    try:
        result = await db.execute(
            select(Prescription).where(Prescription.id == prescription_id)
        )
        row = result.scalar_one_or_none()

        if not row:
            return {"status": "error", "data": None, "message": "Prescription not found"}

        return {
            "status": "success",
            "data": {
                "prescription_id": row.id,
                "session_id": row.session_id,
                "patient_id": row.patient_id,
                "image_path": row.image_path,
                "created_at": row.created_at.isoformat()
            },
            "message": "Prescription fetched"
        }

    except Exception as e:
        return {"status": "error", "data": None, "message": str(e)}


# ─────────────────────────────────────────
# READ ALL BY SESSION
# Called by: GET /api/prescription/session/{session_id}
# Triggered by: Person A fetching all prescriptions for a session
# ─────────────────────────────────────────

async def get_prescriptions_by_session(session_id: str, db: AsyncSession):
    try:
        result = await db.execute(
            select(Prescription).where(
                Prescription.session_id == session_id
            ).order_by(Prescription.created_at.desc())
        )
        rows = result.scalars().all()

        return {
            "status": "success",
            "data": {
                "prescriptions": [
                    {
                        "prescription_id": r.id,
                        "patient_id": r.patient_id,
                        "image_path": r.image_path,
                        "created_at": r.created_at.isoformat()
                    }
                    for r in rows
                ]
            },
            "message": f"{len(rows)} prescription(s) found"
        }

    except Exception as e:
        return {"status": "error", "data": None, "message": str(e)}


# ─────────────────────────────────────────
# UPDATE
# Called by: PATCH /api/prescription/{id}
# Triggered by: Doctor redraws and saves again on canvas page
# ─────────────────────────────────────────

async def update_prescription(
    prescription_id: str,
    image_data: str,
    db: AsyncSession
):
    try:
        result = await db.execute(
            select(Prescription).where(Prescription.id == prescription_id)
        )
        row = result.scalar_one_or_none()

        if not row:
            return {"status": "error", "data": None, "message": "Prescription not found"}

        overwrite_image_on_disk(row.image_path, image_data)

        row.created_at = datetime.utcnow()
        await db.commit()

        return {
            "status": "success",
            "data": {"prescription_id": prescription_id},
            "message": "Prescription updated successfully"
        }

    except Exception as e:
        await db.rollback()
        return {"status": "error", "data": None, "message": str(e)}
    