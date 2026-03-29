from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.enums import ReminderStatus, ReminderType

if TYPE_CHECKING:
    from models.consultation import Consultation
    from models.patient import Patient


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id"), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    type: Mapped[ReminderType] = mapped_column(
        SAEnum(
            ReminderType,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            native_enum=False,
            name="remindertype",
        ),
        nullable=False,
    )
    status: Mapped[ReminderStatus] = mapped_column(
        SAEnum(
            ReminderStatus,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            native_enum=False,
            name="reminderstatus",
        ),
        default=ReminderStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="reminders")
    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="reminders")

    def __repr__(self) -> str:
        return f"<Reminder id={self.id} type={self.type!r} status={self.status!r}>"
