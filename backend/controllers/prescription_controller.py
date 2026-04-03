import base64

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.consultation import Consultation
from models.patient import Patient
from models.pharmacy import Pharmacy
from models.prescription import Prescription
from services.pharmacy_service import assign_pharmacy, notify_patient_about_prescription_status
from services.translate_service import TranslationService
from services.twilio_service import send_whatsapp_message


translator = TranslationService()



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

def _decode_image(image_data: str | None):
    if not image_data:
        return None
    if "," in image_data:
        image_data = image_data.split(",")[1]
    return base64.b64decode(image_data)


def _translate_if_needed(text: str, preferred_language: str | None) -> str:
    language = (preferred_language or "en").strip().lower()
    if language == "si":
        return translator.translate_to_sinhala(text)
    return text


def _build_pharmacy_assignment_message(pharmacy_name: str, preferred_language: str | None) -> str:
    message = (
        f"Your prescription has been assigned to {pharmacy_name}. "
        "The pharmacy will prepare it and update you when needed."
    )
    return _translate_if_needed(message, preferred_language)


async def _notify_patient_about_pharmacy_assignment(
    consultation_id: int,
    pharmacy_id: int,
    db: AsyncSession,
) -> None:
    try:
        consultation_result = await db.execute(
            select(Consultation).where(Consultation.id == consultation_id)
        )
        consultation = consultation_result.scalar_one_or_none()
        if consultation is None:
            return

        patient_result = await db.execute(
            select(Patient).where(Patient.id == consultation.patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        if patient is None or not patient.phone:
            return

        pharmacy_result = await db.execute(
            select(Pharmacy).where(Pharmacy.id == pharmacy_id)
        )
        pharmacy = pharmacy_result.scalar_one_or_none()
        if pharmacy is None:
            return

        send_whatsapp_message(
            to_number=patient.phone,
            message_body=_build_pharmacy_assignment_message(
                pharmacy_name=pharmacy.name,
                preferred_language=patient.preferred_language,
            ),
        )
    except ValueError as e:
        # Log but don't fail prescription save if Twilio is not configured
        print(f"Warning: Could not send WhatsApp notification: {str(e)}")
    except Exception as e:
        # Log but don't fail prescription save if notification fails
        print(f"Warning: Unexpected error sending WhatsApp notification: {str(e)}")


async def save_prescription(consultation_id, pharmacy_id, image_data, image_mime_type, db: AsyncSession):
    try:
        # Always auto-assign based on current pharmacy load.
        pharmacy_id = await assign_pharmacy(db)

        existing = await db.execute(
            select(Prescription).where(Prescription.consultation_id == consultation_id)
        )
        row = existing.scalar_one_or_none()

        img_bytes = _decode_image(image_data) if image_data else None

        if row:
            previous_pharmacy_id = row.pharmacy_id
            if img_bytes:
                row.image_data = img_bytes
            row.pharmacy_id = pharmacy_id
            row.image_mime_type = image_mime_type or "image/png"
            row.status = "pending"

            await db.commit()
            await db.refresh(row)
            if previous_pharmacy_id != pharmacy_id:
                await _notify_patient_about_pharmacy_assignment(
                    consultation_id=consultation_id,
                    pharmacy_id=pharmacy_id,
                    db=db,
                )
            return row

        record = Prescription(
            consultation_id=consultation_id,
            pharmacy_id=pharmacy_id,
            image_data=img_bytes,
            image_mime_type=image_mime_type or "image/png",
            status="pending",
        )

        db.add(record)
        await db.commit()
        await db.refresh(record)
        await _notify_patient_about_pharmacy_assignment(
            consultation_id=consultation_id,
            pharmacy_id=pharmacy_id,
            db=db,
        )
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
        previous_status = row.status
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
        if status and status != previous_status:
            await notify_patient_about_prescription_status(
                db,
                prescription=row,
                status=status,
            )
        return row
    except Exception as e:
        await db.rollback()
        raise e
