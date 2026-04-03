from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.config import settings
from services.scheduler_service import scheduler_service

from routers import auth_router, twilio_router, prescription_router, transcription_router, patient_router, consultation_router, translation_router, pharmacy_router, symptom_triage_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler_service.start()
    try:
        yield
    finally:
        scheduler_service.shutdown()


app = FastAPI(
    title="MediScript API",
    version="0.1.0",
    description="AI-powered clinical communication system for Hemas Hospitals.",
    lifespan=lifespan,
)

@app.get("/")
def root():
    return {"message": "MediScript API", "version": "0.1.0"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=(
        r"^https?://("
        r"localhost|"
        r"127\.0\.0\.1|"
        r"10(?:\.\d{1,3}){3}|"
        r"192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2}"
        r")(:\d+)?$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(prescription_router.router, prefix="/api/prescriptions", tags=["Prescription"]) 

# ── Routers (uncomment as each module is implemented) ─────────────────────────
# from routers import auth_router, patient_router
from routers import transcription_router
# from routers import prescription_router, consultation_router
# from routers import pharmacy_router, translation_router, notification_router

# app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
# app.include_router(consultation_router.router, prefix="/api/consultations", tags=["Consultation"])
app.include_router(transcription_router.router, prefix="/api/transcription", tags=["Transcription"])
# app.include_router(nlp_router.router, prefix="/api/nlp", tags=["NLP"])
# app.include_router(prescription_router.router, prefix="/api/prescriptions", tags=["Prescription"])
app.include_router(pharmacy_router.router, prefix="/api/pharmacy", tags=["Pharmacy"])
# app.include_router(notification_router.router, prefix="/api/notifications", tags=["Notifications"])

app.include_router(twilio_router, prefix="/api")
app.include_router(symptom_triage_router, prefix="/api")
app.include_router(translation_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(patient_router.router, prefix="/api", tags=["Patient"])
app.include_router(consultation_router.router, prefix="/api", tags=["Consultation"])
