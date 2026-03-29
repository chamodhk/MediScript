from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./mediscript.db"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    WHISPER_MODEL: str = "small"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "meditron:7b"
    LIBRETRANSLATE_URL: str = "http://localhost:5000"

    APP_ENV: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
