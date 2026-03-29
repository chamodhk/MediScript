from pydantic import BaseModel


class SendTranscriptionRequest(BaseModel):
    patient_number: str
    transcription: str
