from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from controllers.patient_controller import get_all_patients

router = APIRouter()


@router.get("/patients")
async def fetch_all_patients(db: AsyncSession = Depends(get_db)):
    """Get all patients from the database"""
    return await get_all_patients(db)
