from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from controllers.transcription_controller import TranscriptionController
from core.database import get_db
from models.consultation import Consultation

router = APIRouter()
controller = TranscriptionController()


# ── Transcribe Audio ──────────────────────────────────────────
@router.post("/transcribe/{consultation_id}")
async def transcribe_audio(
    consultation_id: int,
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Read audio bytes from frontend
        audio_bytes = await audio.read()

        # Process through full pipeline
        result = await controller.process_audio(
            audio_bytes=audio_bytes,
            consultation_id=consultation_id,
            db=db
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ── Get Transcript For A Consultation ─────────────────────────
@router.get("/transcribe/{consultation_id}")
async def get_transcript(
    consultation_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Consultation).filter(Consultation.id == consultation_id)
        )
        consultation = result.scalar_one_or_none()

        if not consultation:
            raise HTTPException(
                status_code=404,
                detail="Consultation not found"
            )

        return {
            "status": "success",
            "consultation_id": consultation_id,
            "raw_transcript": consultation.transcript,
            "structured": consultation.structured_output,
            "consultation_status": consultation.status
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )