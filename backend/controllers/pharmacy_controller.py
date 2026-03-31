from io import BytesIO

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from services import pharmacy_service


def _normalize_statuses(status_filter: str) -> list[str]:
	statuses = [item.strip() for item in status_filter.split(",") if item.strip()]
	return statuses or ["pending", "preparing", "ready"]


async def get_queue(
	db: AsyncSession,
	pharmacy_id: int,
	status_filter: str,
) -> list[dict]:
	"""Fetch queue rows from service and shape them for API responses."""
	statuses = _normalize_statuses(status_filter)
	rows = await pharmacy_service.get_queue_items(
		db=db,
		pharmacy_id=pharmacy_id,
		statuses=statuses,
	)

	return [
		{
			"id": row["id"],
			"status": row["status"],
			"created_at": row["created_at"],
			"patient_name": row["patient_name"],
			"patient_phone": row["patient_phone"],
			"consultation_id": row["consultation_id"],
			"image_mime_type": row["image_mime_type"],
		}
		for row in rows
	]


async def get_prescription_image(db: AsyncSession, prescription_id: int) -> StreamingResponse:
	"""Get image payload from service and return a streaming HTTP response."""
	image_data, image_mime_type = await pharmacy_service.get_prescription_image_payload(
		db=db,
		prescription_id=prescription_id,
	)
	return StreamingResponse(BytesIO(image_data), media_type=image_mime_type)


async def update_prescription_status(
	db: AsyncSession,
	prescription_id: int,
	new_status: str,
) -> dict:
	"""Delegate transition validation to service and shape a compact response."""
	updated = await pharmacy_service.advance_status(
		db=db,
		prescription_id=prescription_id,
		requested_status=new_status,
	)
	return {"id": updated.id, "status": updated.status}


async def get_pharmacy_stats(db: AsyncSession, pharmacy_id: int) -> dict:
	"""Return aggregate pharmacy status counts from service."""
	stats = await pharmacy_service.get_pharmacy_stats(db=db, pharmacy_id=pharmacy_id)
	return {
		"pending": int(stats["pending"]),
		"preparing": int(stats["preparing"]),
		"ready": int(stats["ready"]),
		"collected_today": int(stats["collected_today"]),
	}
