from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.consultation import Consultation
    from models.reminder import Reminder


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    recording_consent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default="true")
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    consultations: Mapped[List["Consultation"]] = relationship("Consultation", back_populates="patient")
    reminders: Mapped[List["Reminder"]] = relationship("Reminder", back_populates="patient")

    def __repr__(self) -> str:
        return f"<Patient id={self.id} name={self.name!r} token={self.token!r}>"
