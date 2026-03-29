from typing import Any


class TranslationService:
    def __init__(self) -> None:
        self.translator: Any | None = None
        self.lang_map = {
            "en": "eng_Latn",
            "si": "sin_Sinh",
            "ta": "tam_Taml",
        }

    def _get_translator(self) -> Any:
        if self.translator is None:
            from transformers import pipeline

            self.translator = pipeline(
                "translation",
                model="facebook/nllb-200-distilled-600M",
            )
        return self.translator

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return text

        src_lang = self.lang_map[source]
        tgt_lang = self.lang_map[target]

        result = self._get_translator()(
            text,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            max_length=200,
        )

        return result[0]["translation_text"]
