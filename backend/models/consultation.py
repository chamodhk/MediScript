from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.enums import ConsultationStatus

if TYPE_CHECKING:
    from models.patient import Patient
    from models.prescription import Prescription
    from models.reminder import Reminder
    from models.user import User


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    audio_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[ConsultationStatus] = mapped_column(
        SAEnum(
            ConsultationStatus,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            native_enum=False,
            name="consultationstatus",
        ),
        default=ConsultationStatus.IN_PROGRESS,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="consultations")
    doctor: Mapped["User"] = relationship("User", back_populates="consultations")
    prescription: Mapped[Optional["Prescription"]] = relationship(
        "Prescription", back_populates="consultation", uselist=False
    )
    reminders: Mapped[List["Reminder"]] = relationship("Reminder", back_populates="consultation")

    def __repr__(self) -> str:
        return f"<Consultation id={self.id} patient_id={self.patient_id} doctor_id={self.doctor_id} status={self.status!r}>"
