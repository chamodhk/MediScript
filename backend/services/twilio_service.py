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
