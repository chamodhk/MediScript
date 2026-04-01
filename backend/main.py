from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.config import settings, load_env_file
from routers import auth_router, twilio_router, prescription_router,transcription_router


load_env_file()

app = FastAPI(
    title="MediScript API",
    version="0.1.0",
    description="AI-powered clinical communication system for Hemas Hospitals.",
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

app.mount("/static", StaticFiles(directory="static"), name="static")

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
# app.include_router(translation_router.router, prefix="/api/translation", tags=["Translation"])
# app.include_router(notification_router.router, prefix="/api/notifications", tags=["Notifications"])

app.include_router(twilio_router)
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
