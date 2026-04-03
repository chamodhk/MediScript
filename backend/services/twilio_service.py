import os

from twilio.base.exceptions import TwilioException
from twilio.rest import Client


DEFAULT_WHATSAPP_SANDBOX_NUMBER = "whatsapp:+14155238886"


def _format_whatsapp_number(phone_number: str) -> str:
    """Ensure the number matches Twilio's WhatsApp address format."""
    cleaned_number = phone_number.strip()
    if not cleaned_number:
        raise ValueError("Phone number is required.")

    if cleaned_number.startswith("whatsapp:"):
        return cleaned_number

    return f"whatsapp:{cleaned_number}"


def send_whatsapp_message(
    to_number: str,
    message_body: str,
    from_number: str | None = None,
    media_url: str | None = None,
) -> dict:
    """Send a WhatsApp message using Twilio."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    sender = from_number or os.getenv(
        "TWILIO_WHATSAPP_FROM", DEFAULT_WHATSAPP_SANDBOX_NUMBER
    )

    if not account_sid or not auth_token:
        raise ValueError(
            "Missing Twilio credentials. Set TWILIO_ACCOUNT_SID and "
            "TWILIO_AUTH_TOKEN in your environment."
        )

    if not message_body or not message_body.strip():
        raise ValueError("Message body is required.")

    client = Client(account_sid, auth_token)

    payload = {
        "from_": _format_whatsapp_number(sender),
        "to": _format_whatsapp_number(to_number),
        "body": message_body.strip(),
    }

    if media_url:
        payload["media_url"] = [media_url]

    try:
        message = client.messages.create(**payload)
    except TwilioException as exc:
        raise RuntimeError(f"Failed to send WhatsApp message: {exc}") from exc

    return {
        "sid": message.sid,
        "status": message.status,
        "to": message.to,
        "from": message.from_,
        "body": message.body,
    }


from services.translate_service import TranslationService

translator: TranslationService | None = None


def _get_translator() -> TranslationService:
    global translator
    if translator is None:
        translator = TranslationService()
    return translator


def _translate_text_if_needed(text: str | None, target_language: str) -> str | None:
    if not text or not isinstance(text, str) or not text.strip():
        return text
    if target_language == "en":
        return text
    return _get_translator().translate(text, source="en", target=target_language)


def build_sinhala_message(
    translated_transcript: str,
    consultation_id: int | None = None,
    session_datetime: str | None = None,
    doctor_name: str | None = None,
) -> str:
    lines = []
    lines.append("🏥 *වෛද්‍ය උපදෙස් සාරාංශය*")
    lines.append("")

    if consultation_id is not None:
        lines.append(f"*උපදේශන අංකය:* {consultation_id}")

    if doctor_name:
        lines.append(f"*වෛද්‍යවරයා:* {doctor_name}")

    if session_datetime:
        lines.append(f"*දිනය හා වේලාව:* {session_datetime}")

    if consultation_id is not None or doctor_name or session_datetime:
        lines.append("")

    if translated_transcript and translated_transcript.strip():
        lines.append(translated_transcript.strip())
        lines.append("")
    else:
        lines.append("අමතර උපදෙස් සටහන් වී නොමැත.")
        lines.append("")

    lines.append("අමතර පැහැදිලි කිරීමක් අවශ්‍ය නම් රෝහල අමතන්න.")

    return "\n".join(lines)

def send_structured_whatsapp_message(
    to_number: str,
    structured_data: dict,
    raw_transcript: str | None = None,
    consultation_id: int | None = None,
    session_datetime: str | None = None,
    doctor_name: str | None = None,
    preferred_language: str | None = None,
    from_number: str | None = None,
) -> dict:
    """Send structured consultation output as a formatted WhatsApp message."""
    target_language = (preferred_language or "en").strip().lower()

    def prettify_key(key: str) -> str:
        return key.replace("_", " ").strip().capitalize()

    def prettify_instruction_type(value: str | None) -> str:
        if not value:
            return "Follow-up"
        return value.replace("_", " ").strip().title()

    def format_follow_up_item(value) -> str | None:
        if value is None:
            return None

        if isinstance(value, str):
            text = value.strip()
            return text or None

        if not isinstance(value, dict):
            text = str(value).strip()
            return text or None

        instruction = str(
            value.get("doctor_instruction")
            or value.get("source_text")
            or ""
        ).strip()
        time_reference = str(value.get("medical_time_reference") or "").strip()
        instruction_type = prettify_instruction_type(
            str(value.get("instruction_type") or value.get("type") or "").strip()
        )

        if instruction and time_reference and time_reference.lower() not in instruction.lower():
            return f"{instruction} ({instruction_type}; {time_reference})"

        if instruction:
            return instruction

        if time_reference:
            return f"{instruction_type}: {time_reference}"

        return None

    def flatten_value(value) -> list[str]:
        """
        Convert unknown LLM-shaped data into readable text lines.
        """
        lines = []

        if value is None:
            return lines

        if isinstance(value, str):
            text = value.strip()
            if text:
                lines.append(text)
            return lines

        if isinstance(value, (int, float, bool)):
            lines.append(str(value))
            return lines

        if isinstance(value, list):
            for item in value:
                lines.extend(flatten_value(item))
            return lines

        if isinstance(value, dict):
            formatted_follow_up = format_follow_up_item(value)
            if formatted_follow_up:
                return [formatted_follow_up]

            # Special handling for common follow-up shape
            if set(value.keys()) >= {"type", "when"}:
                follow_type = value.get("type")
                when = value.get("when")
                if follow_type and when:
                    lines.append(f"{str(follow_type).title()}: {when}")
                    return lines

            # Special handling for common medicine shape
            if "medicine_name" in value:
                medicine = value.get("medicine_name", "")
                dosage = value.get("dosage", "")
                frequency = value.get("frequency", "")
                parts = [str(medicine).strip(), str(dosage).strip(), str(frequency).strip()]
                text = " ".join(part for part in parts if part)
                if text:
                    lines.append(f"Take {text}.")
                return lines

            # Generic dict handling
            for k, v in value.items():
                if v is None or v == [] or v == "":
                    continue

                nested_lines = flatten_value(v)

                if not nested_lines:
                    continue

                # If nested value is a simple string-like result, prefix with key label
                if len(nested_lines) == 1:
                    if isinstance(v, (str, int, float, bool)):
                        lines.append(f"{prettify_key(k)}: {nested_lines[0]}")
                    else:
                        lines.extend(nested_lines)
                else:
                    # For grouped lists like additional_advice, dietary_instructions, etc.
                    lines.extend(nested_lines)

            return lines

        lines.append(str(value))
        return lines

    greetings = structured_data.get("greetings")
    heading = structured_data.get("heading")
    instructions = structured_data.get("instructions", [])
    follow_up = structured_data.get("follow_up", [])

    lines = []
    lines.append("🏥 *Consultation Summary*")
    lines.append("")

    if consultation_id is not None:
        lines.append(f"*Consultation ID:* {consultation_id}")

    if doctor_name:
        lines.append(f"*Doctor:* {doctor_name}")

    if session_datetime:
        lines.append(f"*Session Date & Time:* {session_datetime}")

    if consultation_id is not None or doctor_name or session_datetime:
        lines.append("")

    if greetings:
        lines.extend(flatten_value(greetings))
        lines.append("")

    if heading:
        heading_lines = flatten_value(heading)
        if heading_lines:
            lines.append(f"*{heading_lines[0]}*")
            lines.append("")

    instruction_lines = flatten_value(instructions)
    if instruction_lines:
        lines.append("*Instructions:*")
        for item in instruction_lines:
            lines.append(f"• {item}")
        lines.append("")

    follow_up_lines = flatten_value(follow_up)
    if follow_up_lines:
        lines.append("*Follow-up:*")
        for item in follow_up_lines:
            lines.append(f"• {item}")
        lines.append("")

    if not instruction_lines and not follow_up_lines:
        lines.append("No additional instructions were recorded.")
        lines.append("")

    lines.append("Please contact the hospital if you need clarification.")

    message_body = "\n".join(lines)

    if target_language == "si":
        translated_transcript = _translate_text_if_needed(raw_transcript, "si") if raw_transcript else ""
        message_body = build_sinhala_message(
            translated_transcript=translated_transcript,
            consultation_id=consultation_id,
            session_datetime=session_datetime,
            doctor_name=doctor_name,
        )

    return send_whatsapp_message(
        to_number=to_number,
        message_body=message_body,
        from_number=from_number,
    )
