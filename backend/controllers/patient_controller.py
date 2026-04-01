from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.patient import Patient


async def get_all_patients(db: AsyncSession):
    """Fetch all patients from the database"""
    stmt = select(Patient).order_by(Patient.id)
    result = await db.execute(stmt)
    patients = result.scalars().all()
    
    # Convert to dictionaries for JSON response
    return [
        {
            "id": p.id,
            "name": p.name,
            "phone": p.phone,
            "preferred_language": p.preferred_language,
            "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
            "age": p.age,
            "token": p.token,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        }
        for p in patients
    ]
