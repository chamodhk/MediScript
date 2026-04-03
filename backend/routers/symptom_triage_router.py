from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.symptom_triage import SymptomTriageRequest, SymptomTriageResponse
from services.symptom_triage_service import SymptomTriageService


router = APIRouter(prefix="/triage", tags=["triage"])
triage_service = SymptomTriageService()


@router.post("/symptoms", response_model=SymptomTriageResponse)
async def triage_symptoms(
    request: SymptomTriageRequest,
    db: AsyncSession = Depends(get_db),
) -> SymptomTriageResponse:
    return await triage_service.triage(
        db,
        message=request.message,
        patient_name=request.patient_name,
    )
