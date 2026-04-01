from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from controllers.consultation_controller import create_consultation, get_consultation

router = APIRouter()


class ConsultationCreate(BaseModel):
    patient_id: int
    doctor_id: int


@router.post("/consultations")
async def create_new_consultation(
    consultation: ConsultationCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new consultation record"""
    try:
        return await create_consultation(db, consultation.patient_id, consultation.doctor_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/consultations/{consultation_id}")
async def fetch_consultation(
    consultation_id: int, db: AsyncSession = Depends(get_db)
):
    """Get a specific consultation by ID"""
    consultation = await get_consultation(db, consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return consultation
