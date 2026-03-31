from datetime import date, datetime, time
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.consultation import Consultation
from models.patient import Patient
from models.prescription import Prescription
from models.user import User
from routers.auth_router import get_current_user
from services.pharmacy_service import advance_status


router = APIRouter(tags=["Pharmacy"])


class QueueItemResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	status: str
	created_at: datetime
	patient_name: str
	patient_phone: str
	consultation_id: int
	image_mime_type: str


class StatusUpdateRequest(BaseModel):
	status: str


class StatusUpdateResponse(BaseModel):
	id: int
	status: str


class PharmacyStatsResponse(BaseModel):
	pending: int
	preparing: int
	ready: int
	collected_today: int


async def require_pharmacist(current_user: User = Depends(get_current_user)) -> User:
	role_value = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
	if role_value != "pharmacist":
		raise HTTPException(status_code=403, detail="Pharmacist access required")
	return current_user


@router.get("/{pharmacy_id}/queue", response_model=list[QueueItemResponse])
async def get_pharmacy_queue(
	pharmacy_id: int,
	status: str = Query("pending,preparing,ready"),
	db: AsyncSession = Depends(get_db),
	_: User = Depends(require_pharmacist),
) -> list[QueueItemResponse]:
	requested_statuses = [item.strip() for item in status.split(",") if item.strip()]
	if not requested_statuses:
		raise HTTPException(status_code=400, detail="At least one status filter must be provided")

	stmt = (
		select(
			Prescription.id,
			Prescription.status,
			Prescription.created_at,
			Patient.name.label("patient_name"),
			Patient.phone.label("patient_phone"),
			Prescription.consultation_id,
			Prescription.image_mime_type,
		)
		.join(Consultation, Consultation.id == Prescription.consultation_id)
		.join(Patient, Patient.id == Consultation.patient_id)
		.where(Prescription.pharmacy_id == pharmacy_id)
		.where(Prescription.status.in_(requested_statuses))
		.order_by(Prescription.created_at.asc())
	)

	result = await db.execute(stmt)
	rows = result.mappings().all()

	return [QueueItemResponse(**row) for row in rows]


@router.get("/prescriptions/{prescription_id}/image")
async def get_prescription_image(
	prescription_id: int,
	db: AsyncSession = Depends(get_db),
	_: User = Depends(require_pharmacist),
) -> StreamingResponse:
	try:
		stmt = select(Prescription.image_data, Prescription.image_mime_type).where(
			Prescription.id == prescription_id
		)
		result = await db.execute(stmt)
		row = result.first()

		if row is None:
			raise HTTPException(status_code=404, detail="Prescription not found")

		image_data, image_mime_type = row
		if not image_data:
			return JSONResponse(
				status_code=404,
				content={"detail": "No image available for this prescription"},
			)

		return StreamingResponse(BytesIO(image_data), media_type=image_mime_type)
	except HTTPException:
		raise
	except (SQLAlchemyError, ValueError, TypeError):
		return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@router.patch("/prescriptions/{prescription_id}/status", response_model=StatusUpdateResponse)
async def update_prescription_status(
	prescription_id: int,
	body: StatusUpdateRequest,
	db: AsyncSession = Depends(get_db),
	_: User = Depends(require_pharmacist),
) -> StatusUpdateResponse:
	updated = await advance_status(
		db=db,
		prescription_id=prescription_id,
		requested_status=body.status,
	)
	return StatusUpdateResponse(id=updated.id, status=updated.status)


@router.get("/{pharmacy_id}/stats", response_model=PharmacyStatsResponse)
async def get_pharmacy_stats(
	pharmacy_id: int,
	db: AsyncSession = Depends(get_db),
	_: User = Depends(require_pharmacist),
) -> PharmacyStatsResponse:
	start_of_today = datetime.combine(date.today(), time.min)
	updated_or_created_column = getattr(Prescription, "updated_at", Prescription.created_at)

	stmt = select(
		func.coalesce(func.sum(case((Prescription.status == "pending", 1), else_=0)), 0).label("pending"),
		func.coalesce(func.sum(case((Prescription.status == "preparing", 1), else_=0)), 0).label("preparing"),
		func.coalesce(func.sum(case((Prescription.status == "ready", 1), else_=0)), 0).label("ready"),
		func.coalesce(
			func.sum(
				case(
					(
						and_(
							Prescription.status == "collected",
							updated_or_created_column >= start_of_today,
						),
						1,
					),
					else_=0,
				)
			),
			0,
		).label("collected_today"),
	).where(Prescription.pharmacy_id == pharmacy_id)

	result = await db.execute(stmt)
	counts = result.mappings().one()

	return PharmacyStatsResponse(
		pending=int(counts["pending"]),
		preparing=int(counts["preparing"]),
		ready=int(counts["ready"]),
		collected_today=int(counts["collected_today"]),
	)
