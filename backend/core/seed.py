"""
Seed initial data — pharmacies, default users, and demo patients.
Run once from the backend/ directory:
    python -m core.seed
"""
import asyncio
from datetime import date

from sqlalchemy import delete

from core.database import AsyncSessionLocal
from core.security import hash_password
from models.enums import UserRole
from models.pharmacy import Pharmacy
from models.patient import Patient
from models.user import User

PHARMACIES = [
    {"id": 1, "name": "Pharmacy 1", "is_available": True},
    {"id": 2, "name": "Pharmacy 2", "is_available": True},
]

DEFAULT_USERS = [
    {
        "email": "admin@mediscript.com",
        "password": "password@123",
        "full_name": "System Admin",
        "role": UserRole.ADMIN,
    },
    {
        "email": "doctor1@mediscript.com",
        "password": "password@123",
        "full_name": "Dr. One",
        "role": UserRole.DOCTOR,
    },
    {
        "email": "doctor2@mediscript.com",
        "password": "password@123",
        "full_name": "Dr. Two",
        "role": UserRole.DOCTOR,
    },
    {
        "email": "pharmacy1@mediscript.com",
        "password": "password@123",
        "full_name": "Pharmacist One",
        "role": UserRole.PHARMACIST,
    },
    {
        "email": "pharmacy2@mediscript.com",
        "password": "password@123",
        "full_name": "Pharmacist Two",
        "role": UserRole.PHARMACIST,
    },
]

DEMO_PATIENTS = [
    {
        "name": "Kamal Perera",
        "phone": "0771234567",
        "preferred_language": "si",
        "date_of_birth": date(1985, 3, 12),
        "age": 41,
        "token": "T001",
    },
    {
        "name": "Nimal Silva",
        "phone": "0779876543",
        "preferred_language": "si",
        "date_of_birth": date(1972, 7, 25),
        "age": 53,
        "token": "T002",
    },
    {
        "name": "Amara Fernando",
        "phone": "0712345678",
        "preferred_language": "ta",
        "date_of_birth": date(1990, 11, 4),
        "age": 35,
        "token": "T003",
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        # Pharmacies
        for data in PHARMACIES:
            existing = await session.get(Pharmacy, data["id"])
            if not existing:
                session.add(Pharmacy(**data))
                print(f"Seeded pharmacy: {data['name']}")
            else:
                print(f"Already exists: {data['name']}")

        # Users
        allowed_emails = [u["email"] for u in DEFAULT_USERS]
        await session.execute(delete(User).where(User.email.not_in(allowed_emails)))
        print("Removed non-demo users.")

        for u in DEFAULT_USERS:
            result = await session.execute(select(User).where(User.email == u["email"]))
            existing_user = result.scalar_one_or_none()
            if not existing_user:
                session.add(
                    User(
                        email=u["email"],
                        password_hash=hash_password(u["password"]),
                        full_name=u["full_name"],
                        role=u["role"],
                        is_active=True,
                    )
                )
                print(f"Seeded user: {u['email']} ({u['role'].value})")
            else:
                existing_user.password_hash = hash_password(u["password"])
                existing_user.full_name = u["full_name"]
                existing_user.role = u["role"]
                existing_user.is_active = True
                print(f"Updated user: {u['email']} ({u['role'].value})")

        # Demo patients
        for p in DEMO_PATIENTS:
            result = await session.execute(select(Patient).where(Patient.phone == p["phone"]))
            if not result.scalar_one_or_none():
                session.add(Patient(**p))
                print(f"Seeded patient: {p['name']} → token {p['token']}")
            else:
                print(f"Already exists: {p['name']}")

        await session.commit()
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
