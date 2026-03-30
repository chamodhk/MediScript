import os
import uuid
from sqlalchemy.orm import Session
from services.whisper_service import WhisperService
from services.structure_service import StructuringService
from models.consultation import Consultation
from models.enums import ConsultationStatus

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_FOLDER = os.path.join(BASE_DIR, "..", "temp")


class TranscriptionController:

    def __init__(self):
        self.whisper = WhisperService()
        self.structuring = StructuringService()

    async def process_audio(
        self,
        audio_bytes: bytes,
        consultation_id: int,
        db: Session
    ) -> dict:

        # Step 1 - get consultation from DB
        consultation = db.query(Consultation).filter(
            Consultation.id == consultation_id
        ).first()

        if not consultation:
            raise Exception(f"Consultation {consultation_id} not found")

        # Step 2 - save audio to temp
        audio_path = self._save_temp_audio(
            audio_bytes,
            consultation_id
        )

        # Step 3 - save audio path to DB
        consultation.audio_file_path = audio_path
        consultation.status = ConsultationStatus.IN_PROGRESS
        db.commit()

        # Step 4 - Whisper transcribes + deletes audio
        raw_text = self.whisper.transcribe(audio_path)
        print(f"Raw transcript: {raw_text}")

        # Step 5 - update status to TRANSCRIBED
        consultation.transcript = raw_text
        consultation.audio_file_path = None
        consultation.status = ConsultationStatus.TRANSCRIBED
        db.commit()

        # Step 6 - Ollama structures
        structured = self.structuring.structure(raw_text)
        print(f"Structured output: {structured}")

        # Step 7 - update status to STRUCTURED
        consultation.structured_output = structured
        consultation.status = ConsultationStatus.STRUCTURED
        db.commit()

        # Step 8 - return to frontend
        return {
            "status": "success",
            "consultation_id": consultation_id,
            "raw_transcript": raw_text,
            "structured": structured
        }

    def _save_temp_audio(
        self,
        audio_bytes: bytes,
        consultation_id: int
    ) -> str:
        os.makedirs(TEMP_FOLDER, exist_ok=True)
        filename = f"audio_{consultation_id}_{uuid.uuid4().hex}.wav"
        audio_path = os.path.join(TEMP_FOLDER, filename)

        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        return audio_path