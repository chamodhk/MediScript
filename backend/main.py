from fastapi import FastAPI

from backend.config import load_env_file
from backend.routes import twilio_router

load_env_file()

app = FastAPI(title="MediScript WhatsApp Service")
app.include_router(twilio_router)
