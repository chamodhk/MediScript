from fastapi import APIRouter, HTTPException

from models.twilio import SendTranscriptionRequest
from services.twilio_service import send_whatsapp_message


router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.post("/send-transcription")
def send_transcription_whatsapp(request: SendTranscriptionRequest) -> dict:
    try:
        message = send_whatsapp_message(
            to_number=request.patient_number,
            message_body=request.transcription,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "success": True,
        "transcription": request.transcription,
        "message": message,
    }
