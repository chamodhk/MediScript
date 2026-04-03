import json
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


def load_env_file(env_path: str | Path = Path(__file__).resolve().parents[1] / ".env") -> None:
    """Load environment variables from a simple KEY=VALUE file."""
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./mediscript.db"
    # CORS_ORIGINS: List[str] = [
    #     "http://localhost:5173",
    #     "http://127.0.0.1:5173"
    #     ]
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://10.154.40.178:8000",
        "http://10.154.40.178:5173",
        "https://miki-nonexpressive-unloveably.ngrok-free.dev"
    ]
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    WHISPER_MODEL: str = "small"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"
    LIBRETRANSLATE_URL: str = "http://localhost:5000"

    APP_ENV: str = "development"
    REMINDER_TIMEZONE: str = "Asia/Colombo"
    REMINDER_POLL_SECONDS: int = 60

    class Config:
        env_file = ".env"

    @classmethod
    def parse_cors_origins(cls, value: object) -> List[str]:
        if isinstance(value, list):
            return [str(origin).rstrip("/") for origin in value]
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            try:
                parsed = json.loads(raw_value)
            except json.JSONDecodeError:
                parsed = [item.strip() for item in raw_value.split(",") if item.strip()]
            if isinstance(parsed, list):
                return [str(origin).rstrip("/") for origin in parsed]
        return cls.model_fields["CORS_ORIGINS"].default

    def model_post_init(self, __context) -> None:
        self.CORS_ORIGINS = self.parse_cors_origins(self.CORS_ORIGINS)


load_env_file()
settings = Settings()
