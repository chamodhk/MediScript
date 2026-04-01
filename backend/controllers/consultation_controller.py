from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.consultation import Consultation
from models.enums import ConsultationStatus


async def create_consultation(db: AsyncSession, patient_id: int, doctor_id: int):
    """Create a new consultation record"""
    consultation = Consultation(
        patient_id=patient_id,
        doctor_id=doctor_id,
        status=ConsultationStatus.IN_PROGRESS,
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)
    
    return {
        "id": consultation.id,
        "patient_id": consultation.patient_id,
        "doctor_id": consultation.doctor_id,
        "status": consultation.status.value,
        "created_at": consultation.created_at.isoformat(),
    }


async def get_consultation(db: AsyncSession, consultation_id: int):
    """Fetch a specific consultation by ID"""
    stmt = select(Consultation).where(Consultation.id == consultation_id)
    result = await db.execute(stmt)
    consultation = result.scalar_one_or_none()
    
    if not consultation:
        return None
    
    return {
        "id": consultation.id,
        "patient_id": consultation.patient_id,
        "doctor_id": consultation.doctor_id,
        "transcript": consultation.transcript,
        "structured_output": consultation.structured_output,
        "status": consultation.status.value,
        "created_at": consultation.created_at.isoformat(),
    }
