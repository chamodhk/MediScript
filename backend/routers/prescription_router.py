from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.prescription import PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse
from controllers.prescription_controller import (
    save_prescription,
    get_prescription,
    get_prescriptions_by_session,
    update_prescription
)

router = APIRouter(tags=["Prescription"])

@router.post("/prescription", response_model=PrescriptionResponse)
async def create_prescription(body: PrescriptionCreate, db: AsyncSession = Depends(get_db)):
    return await save_prescription(body.session_id, body.patient_id, body.image_data, db)

@router.get("/prescription/session/{session_id}", response_model=PrescriptionResponse)
async def fetch_by_session(session_id: str, db: AsyncSession = Depends(get_db)):
    return await get_prescriptions_by_session(session_id, db)

@router.get("/prescription/{prescription_id}", response_model=PrescriptionResponse)
async def fetch_prescription(prescription_id: str, db: AsyncSession = Depends(get_db)):
    return await get_prescription(prescription_id, db)

@router.patch("/prescription/{prescription_id}", response_model=PrescriptionResponse)
async def edit_prescription(prescription_id: str, body: PrescriptionUpdate, db: AsyncSession = Depends(get_db)):
    return await update_prescription(prescription_id, body.image_data, db)
