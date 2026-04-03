from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.twilio import SendTranscriptionRequest
from services.reminder_flow_service import ReminderFlowService
from services.twilio_service import send_whatsapp_message
from services.whatsapp_channeling_service import WhatsAppChannelingService


router = APIRouter()
reminder_flow_service = ReminderFlowService()
channeling_service = WhatsAppChannelingService()


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


@router.post("/twilio/webhook")
async def handle_twilio_webhook(
    Body: str = Form(default=""),
    From: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        normalized_from = From.replace("whatsapp:", "").strip()
        reply = await channeling_service.handle_message(
            db,
            from_number=normalized_from,
            body=Body,
        )
        if reply is None:
            reply = await reminder_flow_service.handle_incoming_message(
                db,
                from_number=normalized_from,
                body=Body,
            )
        send_whatsapp_message(
            to_number=From,
            message_body=reply,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"success": True}
