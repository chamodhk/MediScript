import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.consultation import Consultation
from models.enums import ConsultationStatus
from models.patient import Patient
from models.user import User
from services.reminder_flow_service import ReminderFlowService
from services.whisper_service import WhisperService
from services.structure_service import StructureService
from services.twilio_service import send_structured_whatsapp_message

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_FOLDER = os.path.join(BASE_DIR, "..", "temp")


class TranscriptionController:

    def __init__(self):
        self.whisper = WhisperService()
        self.structuring = StructureService()
        self.reminder_flow = ReminderFlowService()

    async def process_audio(
        self,
        audio_bytes: bytes,
        consultation_id: int,
        db: AsyncSession
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

        patient_result = await db.execute(
            select(Patient).filter(Patient.id == consultation.patient_id)
        )
        patient = patient_result.scalar_one_or_none()

        if not patient:
            raise Exception(f"Patient {consultation.patient_id} not found")

        doctor_result = await db.execute(
            select(User).filter(User.id == consultation.doctor_id)
        )
        doctor = doctor_result.scalar_one_or_none()

        doctor_name = doctor.full_name if doctor else None
        session_datetime = consultation.created_at.strftime("%Y-%m-%d %I:%M %p")

        send_structured_whatsapp_message(
            to_number=patient.phone,
            structured_data=structured,
            raw_transcript=raw_text,
            consultation_id=consultation.id,
            session_datetime=session_datetime,
            doctor_name=doctor_name,
            preferred_language=patient.preferred_language,
        )
        created_reminders = await self.reminder_flow.create_follow_up_flow(
            db,
            patient=patient,
            consultation=consultation,
            structured_data=structured,
        )

        print(f"✨ [STEP 7] Structured Output Saved to Database")
        print(f"   consultation.structured_output = {str(structured)[:100]}...")
        print(f"   consultation.status = {consultation.status}")
        print(f"   reminders_created = {len(created_reminders)}")
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
