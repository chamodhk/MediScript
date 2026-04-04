import json
import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings


def load_env_file(env_path: str | Path = Path(__file__).resolve().parents[1] / ".env") -> None:
    """Load environment variables from a simple KEY=VALUE file."""
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
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
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://10.154.40.178:8000",
        "http://10.154.40.178:5173",
        "https://miki-nonexpressive-unloveably.ngrok-free.dev"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: object) -> List[str]:
        if isinstance(v, list):
            return [str(o).rstrip("/") for o in v]
        if isinstance(v, str):
            raw = v.strip()
            if not raw:
                return []
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = [item.strip() for item in raw.split(",") if item.strip()]
            if isinstance(parsed, list):
                return [str(o).rstrip("/") for o in parsed]
        return []

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



load_env_file()
settings = Settings()
