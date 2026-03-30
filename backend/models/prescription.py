from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.consultation import Consultation
    from models.pharmacy import Pharmacy


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(
        ForeignKey("consultations.id"), nullable=False, unique=True, index=True
    )
    pharmacy_id: Mapped[int] = mapped_column(ForeignKey("pharmacies.id"), nullable=False, index=True)
    # Optional filesystem path (e.g. duplicate export under static/) — primary payload is image_data
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Raw PNG/JPEG bytes persisted in DB for pharmacy queue and audit
    image_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    image_mime_type: Mapped[str] = mapped_column(String(64), default="image/png", nullable=False)
    # pending | preparing | ready | collected
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    consultation: Mapped["Consultation"] = relationship("Consultation", back_populates="prescription")
    pharmacy: Mapped["Pharmacy"] = relationship("Pharmacy", back_populates="prescriptions")

    def __repr__(self) -> str:
        return f"<Prescription id={self.id} status={self.status!r} pharmacy_id={self.pharmacy_id}>"
