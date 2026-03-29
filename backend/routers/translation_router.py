from fastapi import APIRouter, HTTPException

from backend.models.translation import (
    InstructionTranslationRequest,
    InstructionTranslationResponse,
)
from backend.services.translate_service import TranslationService


router = APIRouter(prefix="/translation", tags=["translation"])
translator = TranslationService()


def normalize(text: str) -> str:
    text = text.strip()
    if not text:
        return text

    text = text[0].upper() + text[1:]
    if text[-1] not in ".!?":
        text += "."
    return text


@router.post("/instructions", response_model=InstructionTranslationResponse)
def translate_instructions(
    data: InstructionTranslationRequest,
) -> InstructionTranslationResponse:
    try:
        cleaned = [normalize(text) for text in data.instructions]
        translated = [
            translator.translate(text, data.source_language, data.target_language)
            for text in cleaned
        ]

        return InstructionTranslationResponse(
            original_instructions=cleaned,
            translated_instructions=translated,
            source_language=data.source_language,
            target_language=data.target_language,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
