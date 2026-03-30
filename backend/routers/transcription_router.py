from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from controllers.transcription_controller import TranscriptionController
from core.database import get_db

router = APIRouter()
controller = TranscriptionController()


# ── Transcribe Audio ──────────────────────────────────────────
@router.post("/transcribe/{consultation_id}")
async def transcribe_audio(
    consultation_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    try:
        from models.consultation import Consultation

        consultation = db.query(Consultation).filter(
            Consultation.id == consultation_id
        ).first()

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