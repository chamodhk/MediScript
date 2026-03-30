from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from core.database import Base          # ← fixed this line
from pydantic import BaseModel
from typing import Optional


# ── SQLAlchemy table ──────────────────────────────
class Prescription(Base):
    __tablename__ = "prescriptions"

    id          = Column(String, primary_key=True)
    session_id  = Column(String, nullable=False)
    patient_id  = Column(String, nullable=False)
    image_path  = Column(String, nullable=False)
    created_at  = Column(DateTime, server_default=func.now())


# ── Pydantic request/response ─────────────────────
class PrescriptionCreate(BaseModel):
    session_id: str
    patient_id: str
    image_data: str

class PrescriptionUpdate(BaseModel):
    image_data: str

class PrescriptionResponse(BaseModel):
    status: str
    data: Optional[dict] = None
    message: str