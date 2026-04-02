from typing import List

from pydantic import BaseModel, Field, field_validator


SUPPORTED_LANGUAGE_CODES = {"en", "si", "ta"}


class InstructionTranslationRequest(BaseModel):
    instructions: List[str] = Field(min_length=1)
    source_language: str = "en"
    target_language: str

    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language_code(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_LANGUAGE_CODES:
            supported = ", ".join(sorted(SUPPORTED_LANGUAGE_CODES))
            raise ValueError(f"Unsupported language code '{value}'. Use one of: {supported}.")
        return normalized


class InstructionTranslationResponse(BaseModel):
    original_instructions: List[str]
    translated_instructions: List[str]
    source_language: str
    target_language: str
