from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
import base64

from core.database import get_db
from models.prescription import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse,
)
from controllers.prescription_controller import (
    save_prescription,
    get_prescription,
    get_prescriptions_by_session,
    update_prescription,
)

router = APIRouter(tags=["Prescription"])


def _build_response(r) -> dict:
    return {
        "id": r.id,
        "consultation_id": r.consultation_id,
        "pharmacy_id": r.pharmacy_id,
        "status": r.status,
        "image_path": r.image_path,
        "image_mime_type": r.image_mime_type,
        "created_at": r.created_at,
        "image_data_b64": (
            f"data:{r.image_mime_type};base64,"
            f"{base64.b64encode(r.image_data).decode()}"
        ) if r.image_data else None,
    }


# ── POST /api/prescriptions/prescription ──────────────────────────────────────
# Called by: React "Save & Attach to Patient Record" button
# Upserts — safe to call multiple times for the same consultation

@router.post("/prescription", response_model=PrescriptionResponse)
async def create_prescription(
    body: PrescriptionCreate,
    db: AsyncSession = Depends(get_db),
):
    record = await save_prescription(
        consultation_id=body.consultation_id,
        pharmacy_id=body.pharmacy_id,
        image_data=body.image_data,
        image_mime_type=body.image_mime_type,
        db=db,
    )
    return _build_response(record)


# ── GET /api/prescriptions/session/{consultation_id} ─────────────────────────
# Called by: React useEffect on mount to restore the latest canvas

@router.get("/session/{consultation_id}", response_model=List[PrescriptionResponse])
async def fetch_by_session(
    consultation_id: int,
    db: AsyncSession = Depends(get_db),
):
    records = await get_prescriptions_by_session(
        consultation_id=consultation_id,
        db=db,
    )
    return [_build_response(r) for r in records]


# ── GET /api/prescriptions/prescription/{prescription_id} ────────────────────
# Called by: pharmacy queue or deep-link by prescription ID

@router.get("/prescription/{prescription_id}", response_model=PrescriptionResponse)
async def fetch_prescription(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
):
    record = await get_prescription(prescription_id=prescription_id, db=db)
    if not record:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return _build_response(record)


# ── PATCH /api/prescriptions/prescription/{prescription_id} ──────────────────
# Called by: pharmacy status updates (pending → preparing → ready → collected)

@router.patch("/prescription/{prescription_id}", response_model=PrescriptionResponse)
async def edit_prescription(
    prescription_id: int,
    body: PrescriptionUpdate,
    db: AsyncSession = Depends(get_db),
):
    record = await update_prescription(
        prescription_id=prescription_id,
        image_data=body.image_data,
        status=body.status,
        db=db,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return _build_response(record)


# ── POST /api/prescriptions/validate ─────────────────────────────────────────
# Called by: React "Validate Handwriting" button
# Stub — wire to Google Vision / AWS Textract when ready

class ValidateRequest(BaseModel):
    image_data: str

@router.post("/validate")
async def validate_handwriting(body: ValidateRequest):
    return {
        "status": "ok",
        "extracted_text": "Validation not yet implemented — wire to OCR service here",
    }