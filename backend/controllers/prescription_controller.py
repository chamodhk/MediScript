from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.prescription import Prescription
import base64



# async def save_prescription(consultation_id, pharmacy_id, image_data, image_mime_type, db: AsyncSession):
#     try:
#         decoded_image = None

#         if image_data:
#             if "," in image_data:
#                 image_data = image_data.split(",")[1]
#             decoded_image = base64.b64decode(image_data)

#         record = Prescription(
#             consultation_id=consultation_id,
#             pharmacy_id=pharmacy_id,
#             image_data=decoded_image,
#             image_mime_type=image_mime_type or "image/png",
#             status="pending"
#         )
#         db.add(record)
#         await db.commit()
#         await db.refresh(record)
#         return record
#     except Exception as e:
#         await db.rollback()
#         raise e
    


# async def save_prescription(consultation_id, pharmacy_id, image_data, image_mime_type, db: AsyncSession):
#     try:
#         record = Prescription(
#             consultation_id=consultation_id,
#             pharmacy_id=pharmacy_id,
#             image_data=image_data.encode() if image_data else None,
#             image_mime_type=image_mime_type or "image/png",
#             status="pending"
#         )
#         db.add(record)
#         await db.commit()
#         await db.refresh(record)
#         return record
#     except Exception as e:
#         await db.rollback()
#         raise e

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.prescription import Prescription
import base64


def _decode_image(image_data: str | None):
    if not image_data:
        return None
    if "," in image_data:
        image_data = image_data.split(",")[1]
    return base64.b64decode(image_data)


async def save_prescription(consultation_id, pharmacy_id, image_data, image_mime_type, db: AsyncSession):
    try:
        existing = await db.execute(
            select(Prescription).where(Prescription.consultation_id == consultation_id)
        )
        row = existing.scalar_one_or_none()

        img_bytes = _decode_image(image_data) if image_data else None

        if row:
            if img_bytes:
                row.image_data = img_bytes
            row.pharmacy_id = pharmacy_id
            row.image_mime_type = image_mime_type or "image/png"
            row.status = "pending"

            await db.commit()
            await db.refresh(row)
            return row

        record = Prescription(
            consultation_id=consultation_id,
            pharmacy_id=pharmacy_id,
            image_data=img_bytes,
            image_mime_type=image_mime_type or "image/png",
            status="pending"
        )

        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    except Exception as e:
        await db.rollback()
        raise e

async def get_prescription(prescription_id: int, db: AsyncSession):
    result = await db.execute(select(Prescription).where(Prescription.id == prescription_id))
    return result.scalar_one_or_none()

async def get_prescriptions_by_session(consultation_id: int, db: AsyncSession):
    result = await db.execute(
        select(Prescription).where(Prescription.consultation_id == consultation_id)
        .order_by(Prescription.created_at.desc())
    )
    return result.scalars().all()

async def update_prescription(prescription_id: int, image_data, status, db: AsyncSession):
    try:
        result = await db.execute(select(Prescription).where(Prescription.id == prescription_id))
        row = result.scalar_one_or_none()
        if not row:
            return None
        # if image_data:
            # row.image_data = image_data.encode()
        if image_data:
            if "," in image_data:
                image_data = image_data.split(",")[1]
            row.image_data = base64.b64decode(image_data)

        if status:
            row.status = status
        await db.commit()
        await db.refresh(row)
        return row
    except Exception as e:
        await db.rollback()
        raise e