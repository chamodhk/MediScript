from typing import List, Optional

from pydantic import BaseModel, Field


class SymptomTriageRequest(BaseModel):
    message: str = Field(min_length=3)
    patient_name: Optional[str] = None


class ConsultantSuggestion(BaseModel):
    doctor_id: int
    doctor_name: str
    category: str
    reason: str


class SymptomTriageResponse(BaseModel):
    category: str
    urgency: str
    urgency_message: str
    extracted_symptoms: List[str]
    matched_keywords: List[str]
    channeling_message: str
    consultants: List[ConsultantSuggestion]
