from fastapi import APIRouter, HTTPException

from backend.models.twilio import SendTranscriptionRequest
from backend.services.service_twilio import send_whatsapp_message


router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.post("/send-transcription")
def send_transcription(request: SendTranscriptionRequest) -> dict:
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
