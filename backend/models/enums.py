from enum import Enum


class UserRole(str, Enum):
    """Application roles stored as VARCHAR in SQLite."""

    ADMIN = "admin"
    DOCTOR = "doctor"
    PHARMACIST = "pharmacist"


class ConsultationStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    TRANSCRIBED = "transcribed"
    STRUCTURED = "structured"
    SUBMITTED = "submitted"


class ReminderType(str, Enum):
    MEDICATION = "medication"
    FOLLOWUP = "followup"
    PROMO = "promo"


class ReminderStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
