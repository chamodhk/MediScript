from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from  typing import List
import base64

from core.database import get_db
from models.prescription import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse
)
from controllers.prescription_controller import (
    save_prescription,
    get_prescription,
    get_prescriptions_by_session,
    update_prescription
)

router = APIRouter(tags=["Prescription"])

@router.post("/prescription", response_model=PrescriptionResponse)
async def create_prescription(body: PrescriptionCreate, db: AsyncSession = Depends(get_db)):
    record = await save_prescription(
        consultation_id=body.consultation_id,
        pharmacy_id=body.pharmacy_id,
        image_data=body.image_data,
        image_mime_type=body.image_mime_type,
        db=db
    )

    return {
        "id": record.id,
        "consultation_id": record.consultation_id,
        "pharmacy_id": record.pharmacy_id,
        "status": record.status,
        "image_path": record.image_path,
        "image_mime_type": record.image_mime_type,
        "image_data_b64": (
            f"data:{record.image_mime_type};base64,"
            f"{base64.b64encode(record.image_data).decode()}"
        ) if record.image_data else None,
        "created_at": record.created_at,
    }


# @router.post("/prescription", response_model=PrescriptionResponse)
# async def create_prescription(body: PrescriptionCreate, db: AsyncSession = Depends(get_db)):
#     return await save_prescription(
#         consultation_id=body.consultation_id,
#         pharmacy_id=body.pharmacy_id,
#         image_data=body.image_data,
#         image_mime_type=body.image_mime_type,
#         db=db
#     )


from typing import List

@router.get("/session/{consultation_id}", response_model=List[PrescriptionResponse])
async def fetch_by_session(
    consultation_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_prescriptions_by_session(
        consultation_id=consultation_id,
        db=db
    )
@router.get("/prescription/{prescription_id}", response_model=PrescriptionResponse)
async def fetch_prescription(prescription_id: int, db: AsyncSession = Depends(get_db)):
    return await get_prescription(prescription_id=prescription_id, db=db)

@router.patch("/prescription/{prescription_id}", response_model=PrescriptionResponse)
async def edit_prescription(prescription_id: int, body: PrescriptionUpdate, db: AsyncSession = Depends(get_db)):
    return await update_prescription(
        prescription_id=prescription_id,
        image_data=body.image_data,
        status=body.status,
        db=db
    )

# ─────────────────────────────────────────
# POST /api/prescription
# Who calls: canvas page "Save & Return" button
# ─────────────────────────────────────────

