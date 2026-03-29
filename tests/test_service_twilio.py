import unittest
from unittest.mock import MagicMock, patch

from twilio.base.exceptions import TwilioException

from backend.services.service_twilio import (
    _format_whatsapp_number,
    send_whatsapp_message,
)


class FormatWhatsAppNumberTests(unittest.TestCase):
    def test_adds_whatsapp_prefix_when_missing(self) -> None:
        self.assertEqual(
            _format_whatsapp_number("+94703086052"),
            "whatsapp:+94703086052",
        )

    def test_keeps_existing_whatsapp_prefix(self) -> None:
        self.assertEqual(
            _format_whatsapp_number("whatsapp:+94703086052"),
            "whatsapp:+94703086052",
        )

    def test_raises_for_empty_phone_number(self) -> None:
        with self.assertRaisesRegex(ValueError, "Phone number is required"):
            _format_whatsapp_number("   ")


class SendWhatsAppMessageTests(unittest.TestCase):
    @patch.dict(
        "os.environ",
        {
            "TWILIO_ACCOUNT_SID": "AC12345678901234567890123456789012",
            "TWILIO_AUTH_TOKEN": "test_auth_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886",
        },
        clear=True,
    )
    @patch("backend.services.service_twilio.Client")
    def test_sends_message_with_expected_payload(self, mock_client_class: MagicMock) -> None:
        mock_message = MagicMock()
        mock_message.sid = "SM123"
        mock_message.status = "queued"
        mock_message.to = "whatsapp:+94703086052"
        mock_message.from_ = "whatsapp:+14155238886"
        mock_message.body = "Hello from a unit test"

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        result = send_whatsapp_message(
            to_number="+94703086052",
            message_body=" Hello from a unit test ",
        )

        mock_client_class.assert_called_once_with(
            "AC12345678901234567890123456789012",
            "test_auth_token",
        )
        mock_client.messages.create.assert_called_once_with(
            from_="whatsapp:+14155238886",
            to="whatsapp:+94703086052",
            body="Hello from a unit test",
        )
        self.assertEqual(
            result,
            {
                "sid": "SM123",
                "status": "queued",
                "to": "whatsapp:+94703086052",
                "from": "whatsapp:+14155238886",
                "body": "Hello from a unit test",
            },
        )

    @patch.dict(
        "os.environ",
        {
            "TWILIO_ACCOUNT_SID": "AC12345678901234567890123456789012",
            "TWILIO_AUTH_TOKEN": "test_auth_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886",
        },
        clear=True,
    )
    @patch("backend.services.service_twilio.Client")
    def test_includes_media_url_when_provided(self, mock_client_class: MagicMock) -> None:
        mock_message = MagicMock()
        mock_message.sid = "SM456"
        mock_message.status = "queued"
        mock_message.to = "whatsapp:+94703086052"
        mock_message.from_ = "whatsapp:+14155238886"
        mock_message.body = "Image message"

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        send_whatsapp_message(
            to_number="+94703086052",
            message_body="Image message",
            media_url="https://example.com/image.png",
        )

        mock_client.messages.create.assert_called_once_with(
            from_="whatsapp:+14155238886",
            to="whatsapp:+94703086052",
            body="Image message",
            media_url=["https://example.com/image.png"],
        )

    @patch.dict("os.environ", {}, clear=True)
    def test_raises_when_credentials_are_missing(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing Twilio credentials"):
            send_whatsapp_message(
                to_number="+94703086052",
                message_body="Hello",
            )

    @patch.dict(
        "os.environ",
        {
            "TWILIO_ACCOUNT_SID": "AC12345678901234567890123456789012",
            "TWILIO_AUTH_TOKEN": "test_auth_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886",
        },
        clear=True,
    )
    def test_raises_when_message_body_is_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "Message body is required"):
            send_whatsapp_message(
                to_number="+94703086052",
                message_body="   ",
            )

    @patch.dict(
        "os.environ",
        {
            "TWILIO_ACCOUNT_SID": "AC12345678901234567890123456789012",
            "TWILIO_AUTH_TOKEN": "test_auth_token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886",
        },
        clear=True,
    )
    @patch("backend.services.service_twilio.Client")
    def test_wraps_twilio_errors(self, mock_client_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = TwilioException("Twilio failure")
        mock_client_class.return_value = mock_client

        with self.assertRaisesRegex(RuntimeError, "Failed to send WhatsApp message"):
            send_whatsapp_message(
                to_number="+94703086052",
                message_body="Hello",
            )


if __name__ == "__main__":
    unittest.main()
