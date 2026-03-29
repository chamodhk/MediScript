from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.prescription import Prescription


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    prescriptions: Mapped[List["Prescription"]] = relationship("Prescription", back_populates="pharmacy")

    def __repr__(self) -> str:
        return f"<Pharmacy id={self.id} name={self.name!r} available={self.is_available}>"
