from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.config import settings, load_env_file
from routers import auth_router, twilio_router, prescription_router, transcription_router, patient_router, consultation_router, translation_router
from services.scheduler_service import scheduler_service


load_env_file()

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
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
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
# app.include_router(pharmacy_router.router, prefix="/api/pharmacy", tags=["Pharmacy"])
# app.include_router(notification_router.router, prefix="/api/notifications", tags=["Notifications"])

app.include_router(twilio_router)
app.include_router(translation_router)
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(patient_router.router, prefix="/api", tags=["Patient"])
app.include_router(consultation_router.router, prefix="/api", tags=["Consultation"])
