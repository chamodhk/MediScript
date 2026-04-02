import re

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class TranslationService:
    def __init__(self) -> None:
        # Sinhala-tuned NLLB checkpoint for English <-> Sinhala use in this app.
        self.model_name = "zaanind/nllb-ensi-v1.6"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        self.lang_map = {
            "en": "eng_Latn",
            "si": "sin_Sinh",
        }

    def translate(self, text: str, source: str = "en", target: str = "si") -> str:
        if not text or not text.strip():
            return text

        source_lang = source.strip().lower()
        target_lang = target.strip().lower()

        if source_lang == target_lang:
            return text

        if source_lang not in self.lang_map:
            raise ValueError(f"Unsupported source language: {source_lang}")
        if target_lang not in self.lang_map:
            raise ValueError(f"Unsupported target language: {target_lang}")

        if source_lang == "en" and target_lang == "si":
            return self.translate_to_sinhala(text)

        self.tokenizer.src_lang = self.lang_map[source_lang]
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        translated_tokens = self.model.generate(
            **inputs,
            forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(self.lang_map[target_lang]),
            max_length=512,
        )

        return self.tokenizer.batch_decode(
            translated_tokens,
            skip_special_tokens=True,
        )[0]

    def translate_to_sinhala(self, text: str) -> str:
        if not text or not text.strip():
            return text

        normalized_text = self._normalize_whitespace(text)
        sentences = self._split_sentences(normalized_text)

        if not sentences:
            return ""

        translated_sentences = [
            self._translate_sentence_to_sinhala(sentence)
            for sentence in sentences
            if sentence.strip()
        ]

        return " ".join(translated_sentences).strip()

    def _translate_sentence_to_sinhala(self, sentence: str) -> str:
        self.tokenizer.src_lang = self.lang_map["en"]
        inputs = self.tokenizer(
            sentence,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        translated_tokens = self.model.generate(
            **inputs,
            forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(self.lang_map["si"]),
            max_length=512,
        )

        translated = self.tokenizer.batch_decode(
            translated_tokens,
            skip_special_tokens=True,
        )[0]

        return self._ensure_sentence_punctuation(translated, sentence)

    def _normalize_whitespace(self, text: str) -> str:
        text = text.replace("\r", "\n")
        text = re.sub(r"\s*\n\s*", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _split_sentences(self, text: str) -> list[str]:
        if not text:
            return []

        if not re.search(r"[.!?]", text):
            return [text.strip()]

        parts = re.split(r"(?<=[.!?])\s+", text)
        return [part.strip() for part in parts if part.strip()]

    def _ensure_sentence_punctuation(self, translated: str, original: str) -> str:
        translated = translated.strip()
        original = original.strip()

        if not translated:
            return translated

        punctuation_map = {
            ".": ".",
            "!": "!",
            "?": "?",
        }
        terminal_punctuation = punctuation_map.get(original[-1])

        if terminal_punctuation:
            translated = translated.rstrip("።॥।.!?…")
            translated = f"{translated}{terminal_punctuation}"

        return translated
