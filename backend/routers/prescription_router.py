from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.prescription import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse
)
from controllers.prescription_controller import (
    save_prescription,
    get_prescription,
    get_prescriptions_by_session,
    update_prescription
)

router = APIRouter(prefix="/api", tags=["Prescription"])


# ─────────────────────────────────────────
# POST /api/prescription
# Who calls: canvas page "Save & Return" button
# ─────────────────────────────────────────

@router.post("/prescription", response_model=PrescriptionResponse)
async def create_prescription(
    body: PrescriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    return await save_prescription(
        session_id=body.session_id,
        patient_id=body.patient_id,
        image_data=body.image_data,
        db=db
    )


# ─────────────────────────────────────────
# GET /api/prescription/session/{session_id}
# Who calls: Person A — get all prescriptions for a session
# NOTE: this route must be ABOVE /{prescription_id}
# so FastAPI does not confuse "session" as an ID
# ─────────────────────────────────────────

@router.get("/prescription/session/{session_id}", response_model=PrescriptionResponse)
async def fetch_by_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await get_prescriptions_by_session(session_id=session_id, db=db)


# ─────────────────────────────────────────
# GET /api/prescription/{prescription_id}
# Who calls: Person A — get one specific prescription
# ─────────────────────────────────────────

@router.get("/prescription/{prescription_id}", response_model=PrescriptionResponse)
async def fetch_prescription(
    prescription_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await get_prescription(prescription_id=prescription_id, db=db)


# ─────────────────────────────────────────
# PATCH /api/prescription/{prescription_id}
# Who calls: canvas page if doctor redraws
# ─────────────────────────────────────────

@router.patch("/prescription/{prescription_id}", response_model=PrescriptionResponse)
async def edit_prescription(
    prescription_id: str,
    body: PrescriptionUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await update_prescription(
        prescription_id=prescription_id,
        image_data=body.image_data,
        db=db
    )