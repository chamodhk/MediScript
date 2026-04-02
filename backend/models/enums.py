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
    AWAITING_PATIENT_CHOICE = "awaiting_patient_choice"
    AWAITING_SCHEDULE_CHOICE = "awaiting_schedule_choice"
    DECLINED = "declined"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ReminderMode(str, Enum):
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    WINDOW = "window"
    CONDITIONAL = "conditional"
