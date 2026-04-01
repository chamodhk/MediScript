import os
import uuid
from sqlalchemy.orm import Session
from services.whisper_service import WhisperService
from services.structure_service import StructureService
from models.consultation import Consultation
from models.enums import ConsultationStatus
from sqlalchemy import select

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_FOLDER = os.path.join(BASE_DIR, "..", "temp")


class TranscriptionController:

    def __init__(self):
        self.whisper = WhisperService()
        self.structuring = StructureService()

    async def process_audio(
        self,
        audio_bytes: bytes,
        consultation_id: int,
        db: Session
    ) -> dict:

        # Step 1 - get consultation from DB
        result = await db.execute(select(Consultation).filter(
            Consultation.id == consultation_id
        ))
        consultation = result.scalar_one_or_none()

        if not consultation:
            raise Exception(f"Consultation {consultation_id} not found")

        print(f"\n{'='*60}")
        print(f"🎤 [STEP 1] Consultation Found")
        print(f"   Consultation ID: {consultation_id}")
        print(f"   Patient ID: {consultation.patient_id}")
        print(f"   Doctor ID: {consultation.doctor_id}")
        print(f"   Current Status: {consultation.status}")
        print(f"{'='*60}\n")

        # Step 2 - save audio to temp
        audio_path = self._save_temp_audio(
            audio_bytes,
            consultation_id
        )

        print(f"💾 [STEP 2] Audio Saved to Temp")
        print(f"   Path: {audio_path}")
        print(f"   Size: {len(audio_bytes) / 1024:.2f} KB\n")

        # Step 3 - save audio path to DB
        consultation.audio_file_path = audio_path
        consultation.status = ConsultationStatus.IN_PROGRESS
        await db.commit()

        print(f"📝 [STEP 3] Audio Path Saved to Database")
        print(f"   consultation.audio_file_path = {audio_path}")
        print(f"   consultation.status = {consultation.status}\n")

        # Step 4 - Whisper transcribes + deletes audio
        print(f"⏳ [STEP 4] Transcription In Progress...")
        raw_text = self.whisper.transcribe(audio_path)
        print(f"✅ Transcription Complete!")
        print(f"   Length: {len(raw_text)} characters")
        print(f"   Preview: {raw_text[:100]}...\n")

        # Step 5 - update status to TRANSCRIBED
        consultation.transcript = raw_text
        consultation.audio_file_path = None  # Audio file deleted after transcription
        consultation.status = ConsultationStatus.TRANSCRIBED
        await db.commit()

        print(f"📚 [STEP 5] Transcript Stored in Database")
        print(f"   consultation.transcript = '{raw_text[:50]}...'")
        print(f"   consultation.audio_file_path = None (audio deleted)")
        print(f"   consultation.status = {consultation.status}\n")

        # Step 6 - Ollama structures
        print(f"🤖 [STEP 6] Structuring With Ollama...")
        structured = self.structuring.structure(raw_text)
        print(f"✅ Structuring Complete!")
        print(f"   Output Type: {type(structured)}")
        print(f"   Output Keys: {list(structured.keys()) if isinstance(structured, dict) else 'N/A'}\n")

        # Step 7 - update status to STRUCTURED
        consultation.structured_output = structured
        consultation.status = ConsultationStatus.STRUCTURED
        await db.commit()

        print(f"✨ [STEP 7] Structured Output Saved to Database")
        print(f"   consultation.structured_output = {str(structured)[:100]}...")
        print(f"   consultation.status = {consultation.status}")
        print(f"{'='*60}\n")

        # Step 8 - return to frontend
        print(f"🎉 [STEP 8] Returning Response to Frontend\n")
        
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