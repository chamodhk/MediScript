from __future__ import annotations

import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.config import settings
from models.consultation import Consultation
from models.enums import ReminderMode, ReminderStatus, ReminderType
from models.patient import Patient
from models.reminder import Reminder
from services.translate_service import TranslationService
from services.twilio_service import send_whatsapp_message


YES_CHOICES = {"1", "yes", "y"}
NO_CHOICES = {"2", "no", "n"}
DONE_CHOICES = {"done"}
CANCEL_CHOICES = {"cancel", "stop"}


class ReminderService:
    def __init__(self) -> None:
        self.timezone = ZoneInfo(settings.REMINDER_TIMEZONE)
        self._translator: TranslationService | None = None

    async def create_follow_up_reminders(
        self,
        db: AsyncSession,
        *,
        patient: Patient,
        consultation: Consultation,
        structured_data: dict | None,
    ) -> list[Reminder]:
        follow_up_items = structured_data.get("follow_up", []) if isinstance(structured_data, dict) else []
        normalized_follow_ups = self._deduplicate_follow_up(follow_up_items)
        if not normalized_follow_ups:
            return []

        existing_result = await db.execute(
            select(Reminder).where(Reminder.consultation_id == consultation.id)
        )
        existing_keys = {
            self._dedupe_key(reminder.instruction_type, reminder.doctor_instruction, reminder.source_text)
            for reminder in existing_result.scalars().all()
        }

        created_reminders: list[Reminder] = []
        reference_time = self._ensure_timezone(consultation.created_at)

        for item in normalized_follow_ups:
            reminder = self._build_reminder_record(
                patient=patient,
                consultation=consultation,
                item=item,
                reference_time=reference_time,
            )
            if reminder is None:
                continue

            dedupe_key = self._dedupe_key(
                reminder.instruction_type,
                reminder.doctor_instruction,
                reminder.source_text,
            )
            if dedupe_key in existing_keys:
                continue

            db.add(reminder)
            created_reminders.append(reminder)
            existing_keys.add(dedupe_key)

        if created_reminders:
            await db.commit()
            for reminder in created_reminders:
                await db.refresh(reminder)
                self.send_initial_prompt(reminder, patient.phone, patient.preferred_language)

        return created_reminders

    async def handle_incoming_reply(
        self,
        db: AsyncSession,
        *,
        from_number: str,
        body: str,
    ) -> str:
        patient_result = await db.execute(select(Patient).where(Patient.phone == from_number))
        patient = patient_result.scalar_one_or_none()
        if patient is None:
            return "We could not find your patient record for this number."

        text = (body or "").strip()
        normalized = text.lower()

        active_result = await db.execute(
            select(Reminder)
            .where(
                Reminder.patient_id == patient.id,
                Reminder.status.in_(
                    [
                        ReminderStatus.AWAITING_PATIENT_CHOICE,
                        ReminderStatus.AWAITING_SCHEDULE_CHOICE,
                        ReminderStatus.SCHEDULED,
                    ]
                ),
            )
            .order_by(Reminder.created_at.desc())
        )
        active_reminders = active_result.scalars().all()
        if not active_reminders:
            return "There are no active reminder requests for this number right now."

        if normalized in DONE_CHOICES:
            scheduled = next(
                (reminder for reminder in active_reminders if reminder.status == ReminderStatus.SCHEDULED),
                None,
            )
            if scheduled is None:
                return "There is no scheduled reminder to mark as done right now."
            scheduled.status = ReminderStatus.COMPLETED
            await db.commit()
            return self._translate_for_patient(
                "Thank you. We have marked this reminder as completed.",
                patient.preferred_language,
            )

        if normalized in CANCEL_CHOICES:
            reminder = active_reminders[0]
            reminder.status = ReminderStatus.CANCELLED
            await db.commit()
            return self._translate_for_patient(
                "Your reminder has been cancelled.",
                patient.preferred_language,
            )

        reminder = active_reminders[0]
        if reminder.status == ReminderStatus.AWAITING_PATIENT_CHOICE:
            return await self._handle_initial_choice(db, reminder, patient, normalized)

        if reminder.status == ReminderStatus.AWAITING_SCHEDULE_CHOICE:
            return await self._handle_schedule_choice(db, reminder, patient, normalized)

        return self._translate_for_patient(
            "Reply DONE once you have completed it, or CANCEL if you no longer want reminders.",
            patient.preferred_language,
        )

    async def send_due_reminders(self, db: AsyncSession) -> int:
        now = datetime.now(self.timezone).replace(tzinfo=None, second=0, microsecond=0)
        result = await db.execute(
            select(Reminder)
            .options(selectinload(Reminder.patient))
            .where(
                Reminder.status == ReminderStatus.SCHEDULED,
                Reminder.scheduled_at.is_not(None),
                Reminder.scheduled_at <= now,
            )
            .order_by(Reminder.scheduled_at.asc())
        )
        reminders = result.scalars().all()

        sent_count = 0
        for reminder in reminders:
            try:
                send_whatsapp_message(
                    to_number=reminder.patient.phone,
                    message_body=reminder.message or self._build_final_reminder_message(reminder),
                )
                reminder.sent_at = now
                sent_count += 1

                if reminder.patient_reminder_choice == "daily_until_done":
                    next_run = (now + timedelta(days=1)).replace(second=0, microsecond=0)
                    if reminder.medical_window_end and next_run > reminder.medical_window_end:
                        reminder.status = ReminderStatus.COMPLETED
                    else:
                        reminder.scheduled_at = next_run
                else:
                    reminder.status = ReminderStatus.COMPLETED
            except Exception:
                reminder.status = ReminderStatus.FAILED

        if reminders:
            await db.commit()

        return sent_count

    def send_initial_prompt(
        self,
        reminder: Reminder,
        patient_phone: str,
        preferred_language: str | None,
    ) -> None:
        message = self._build_initial_prompt(reminder, preferred_language)
        send_whatsapp_message(to_number=patient_phone, message_body=message)

    def _build_reminder_record(
        self,
        *,
        patient: Patient,
        consultation: Consultation,
        item: dict | str,
        reference_time: datetime,
    ) -> Reminder | None:
        normalized = self._normalize_follow_up_item(item, reference_time)
        instruction_type = normalized["instruction_type"]
        doctor_instruction = normalized["doctor_instruction"]
        if not doctor_instruction:
            return None

        return Reminder(
            patient_id=patient.id,
            consultation_id=consultation.id,
            message=None,
            instruction_type=instruction_type,
            doctor_instruction=doctor_instruction,
            medical_time_reference=normalized["medical_time_reference"],
            medical_window_start=normalized["medical_window_start"],
            medical_window_end=normalized["medical_window_end"],
            exact_medical_datetime=normalized["exact_medical_datetime"],
            patient_reminder_choice=None,
            reminder_mode=normalized["reminder_mode"],
            source_text=normalized["source_text"],
            scheduled_at=None,
            sent_at=None,
            type=ReminderType.FOLLOWUP,
            status=ReminderStatus.AWAITING_PATIENT_CHOICE,
        )

    def _normalize_follow_up_item(self, item: dict | str, reference_time: datetime) -> dict:
        if isinstance(item, dict):
            instruction_type = str(
                item.get("instruction_type") or item.get("type") or "follow_up"
            ).strip()
            doctor_instruction = str(
                item.get("doctor_instruction")
                or item.get("source_text")
                or item.get("message")
                or item.get("when")
                or ""
            ).strip()
            medical_time_reference = str(
                item.get("medical_time_reference") or item.get("when") or ""
            ).strip() or None
            source_text = str(item.get("source_text") or doctor_instruction).strip() or None
            exact_medical_datetime = self._parse_explicit_datetime(
                item.get("exact_medical_datetime") or item.get("reminder_at"),
                medical_time_reference,
                reference_time,
            )
            medical_window_start = self._parse_iso_datetime(item.get("medical_window_start"))
            medical_window_end = self._parse_iso_datetime(item.get("medical_window_end"))
            reminder_mode = self._determine_mode(
                item.get("reminder_mode"),
                medical_time_reference,
                exact_medical_datetime,
            )
        else:
            instruction_type = "follow_up"
            doctor_instruction = str(item).strip()
            medical_time_reference = doctor_instruction or None
            source_text = doctor_instruction or None
            exact_medical_datetime = self._parse_explicit_datetime(None, medical_time_reference, reference_time)
            medical_window_start = None
            medical_window_end = None
            reminder_mode = self._determine_mode(None, medical_time_reference, exact_medical_datetime)

        derived_start, derived_end = self._derive_window_bounds(
            medical_time_reference,
            reference_time,
            medical_window_start,
            medical_window_end,
        )
        medical_window_start = medical_window_start or derived_start
        medical_window_end = medical_window_end or derived_end

        return {
            "instruction_type": instruction_type,
            "doctor_instruction": doctor_instruction,
            "medical_time_reference": medical_time_reference,
            "medical_window_start": medical_window_start,
            "medical_window_end": medical_window_end,
            "exact_medical_datetime": exact_medical_datetime,
            "reminder_mode": reminder_mode,
            "source_text": source_text,
        }

    def _build_initial_prompt(self, reminder: Reminder, preferred_language: str | None) -> str:
        base = f"Your doctor advised: {reminder.doctor_instruction or 'a follow-up action'}."
        if reminder.medical_time_reference:
            base = f"{base} Time reference: {reminder.medical_time_reference}."
        base = f"{base} Would you like a WhatsApp reminder?\n1 = Yes\n2 = No"
        return self._translate_for_patient(base, preferred_language)

    def _build_schedule_prompt(self, reminder: Reminder, preferred_language: str | None) -> str:
        options = self._get_schedule_options(reminder)
        lines = ["When would you like to be reminded?"]
        for index, option in enumerate(options, start=1):
            lines.append(f"{index} = {option['label']}")
        lines.append("Reply with the number.")
        return self._translate_for_patient("\n".join(lines), preferred_language)

    def _build_confirmation_message(self, reminder: Reminder, preferred_language: str | None) -> str:
        if reminder.patient_reminder_choice == "daily_until_done":
            text = (
                f"We will remind you daily about this instruction: {reminder.doctor_instruction}. "
                "Reply DONE when you have completed it."
            )
        else:
            text = (
                f"Your reminder has been scheduled for {self._format_datetime(reminder.scheduled_at)}. "
                f"Instruction: {reminder.doctor_instruction}. Reply DONE when completed."
            )
        return self._translate_for_patient(text, preferred_language)

    def _build_final_reminder_message(self, reminder: Reminder) -> str:
        text = f"Reminder: {reminder.doctor_instruction}."
        if reminder.medical_time_reference:
            text = f"{text} Medical time reference: {reminder.medical_time_reference}."
        return text

    async def _handle_initial_choice(
        self,
        db: AsyncSession,
        reminder: Reminder,
        patient: Patient,
        normalized: str,
    ) -> str:
        if normalized in YES_CHOICES:
            reminder.status = ReminderStatus.AWAITING_SCHEDULE_CHOICE
            await db.commit()
            return self._build_schedule_prompt(reminder, patient.preferred_language)

        if normalized in NO_CHOICES:
            reminder.status = ReminderStatus.DECLINED
            await db.commit()
            return self._translate_for_patient(
                "Okay, we will not send a reminder for this instruction.",
                patient.preferred_language,
            )

        return self._build_initial_prompt(reminder, patient.preferred_language)

    async def _handle_schedule_choice(
        self,
        db: AsyncSession,
        reminder: Reminder,
        patient: Patient,
        normalized: str,
    ) -> str:
        options = self._get_schedule_options(reminder)
        if normalized not in {str(index) for index in range(1, len(options) + 1)}:
            return self._build_schedule_prompt(reminder, patient.preferred_language)

        selected = options[int(normalized) - 1]
        scheduled_at = self._resolve_patient_choice_datetime(reminder, selected["key"])
        if scheduled_at is None:
            return self._translate_for_patient(
                "We could not safely schedule that reminder. Please reply with a different option.",
                patient.preferred_language,
            )

        reminder.patient_reminder_choice = selected["key"]
        reminder.scheduled_at = scheduled_at.replace(tzinfo=None)
        reminder.message = self._translate_for_patient(
            self._build_final_reminder_message(reminder),
            patient.preferred_language,
        )
        reminder.status = ReminderStatus.SCHEDULED
        await db.commit()

        return self._build_confirmation_message(reminder, patient.preferred_language)

    def _get_schedule_options(self, reminder: Reminder) -> list[dict[str, str]]:
        if reminder.exact_medical_datetime is not None:
            return [
                {"key": "morning_of", "label": "Morning of the appointment"},
                {"key": "two_hours_before", "label": "2 hours before"},
                {"key": "exact_time", "label": "At the appointment time"},
            ]

        window_days = self._window_days(reminder)
        if reminder.reminder_mode == ReminderMode.WINDOW and window_days is not None and window_days <= 3:
            return [
                {"key": "tomorrow_morning", "label": "Tomorrow morning"},
                {"key": "tomorrow_evening", "label": "Tomorrow evening"},
                {"key": "two_days_later", "label": "2 days later"},
                {"key": "daily_until_done", "label": "Daily until done"},
            ]

        if reminder.reminder_mode in {ReminderMode.WINDOW, ReminderMode.RELATIVE} and (
            window_days is None or window_days <= 7
        ):
            return [
                {"key": "in_3_days", "label": "In 3 days"},
                {"key": "in_5_days", "label": "In 5 days"},
                {"key": "on_last_day", "label": "On the last day"},
                {"key": "daily_until_done", "label": "Daily until done"},
            ]

        return [
            {"key": "tomorrow_morning", "label": "Tomorrow morning"},
            {"key": "in_3_days", "label": "In 3 days"},
            {"key": "in_1_week", "label": "In 1 week"},
            {"key": "daily_until_done", "label": "Daily until done"},
        ]

    def _resolve_patient_choice_datetime(
        self,
        reminder: Reminder,
        choice_key: str,
    ) -> datetime | None:
        now = datetime.now(self.timezone).replace(second=0, microsecond=0)
        exact = self._ensure_timezone(reminder.exact_medical_datetime) if reminder.exact_medical_datetime else None

        if choice_key == "morning_of" and exact is not None:
            return exact.replace(hour=8, minute=0, second=0, microsecond=0)
        if choice_key == "two_hours_before" and exact is not None:
            return exact - timedelta(hours=2)
        if choice_key == "exact_time" and exact is not None:
            return exact

        if choice_key == "tomorrow_morning":
            return self._combine_date_time(now + timedelta(days=1), time(hour=9, minute=0))
        if choice_key == "tomorrow_evening":
            return self._combine_date_time(now + timedelta(days=1), time(hour=18, minute=0))
        if choice_key == "two_days_later":
            return self._combine_date_time(now + timedelta(days=2), time(hour=9, minute=0))
        if choice_key == "in_3_days":
            return self._combine_date_time(now + timedelta(days=3), time(hour=9, minute=0))
        if choice_key == "in_5_days":
            return self._combine_date_time(now + timedelta(days=5), time(hour=9, minute=0))
        if choice_key == "in_1_week":
            return self._combine_date_time(now + timedelta(days=7), time(hour=9, minute=0))
        if choice_key == "on_last_day":
            if reminder.medical_window_end is None:
                return None
            return self._combine_date_time(self._ensure_timezone(reminder.medical_window_end), time(hour=9, minute=0))
        if choice_key == "daily_until_done":
            return self._combine_date_time(now + timedelta(days=1), time(hour=9, minute=0))

        return None

    def _parse_explicit_datetime(
        self,
        explicit_value: str | None,
        time_reference: str | None,
        reference_time: datetime,
    ) -> datetime | None:
        parsed_iso = self._parse_iso_datetime(explicit_value)
        if parsed_iso is not None:
            return parsed_iso

        reference = (time_reference or "").strip().lower()
        if not reference:
            return None

        time_value = self._extract_clock_time(reference)
        if not time_value:
            return None

        if "tomorrow" in reference:
            return self._combine_date_time(reference_time + timedelta(days=1), time_value)

        weekday_match = re.search(
            r"\b(?:next\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            reference,
        )
        if weekday_match:
            weekday_index = self._weekday_index(weekday_match.group(1))
            days_ahead = (weekday_index - reference_time.weekday()) % 7
            if days_ahead == 0 or "next" in reference:
                days_ahead += 7
            return self._combine_date_time(reference_time + timedelta(days=days_ahead), time_value)

        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", reference)
        if date_match:
            try:
                date_value = datetime.strptime(date_match.group(1), "%Y-%m-%d").replace(tzinfo=self.timezone)
            except ValueError:
                return None
            return self._combine_date_time(date_value, time_value)

        return None

    def _derive_window_bounds(
        self,
        medical_time_reference: str | None,
        reference_time: datetime,
        existing_start: datetime | None,
        existing_end: datetime | None,
    ) -> tuple[datetime | None, datetime | None]:
        if existing_start or existing_end:
            return existing_start, existing_end

        reference = (medical_time_reference or "").strip().lower()
        if not reference:
            return None, None

        match = re.search(r"\bwithin\s+(\d+)\s+(day|days|week|weeks|month|months)\b", reference)
        if not match:
            return None, None

        amount = int(match.group(1))
        unit = match.group(2)
        if "day" in unit:
            delta = timedelta(days=amount)
        elif "week" in unit:
            delta = timedelta(weeks=amount)
        else:
            delta = timedelta(days=30 * amount)

        return reference_time, reference_time + delta

    def _determine_mode(
        self,
        explicit_mode: str | None,
        medical_time_reference: str | None,
        exact_medical_datetime: datetime | None,
    ) -> ReminderMode:
        if exact_medical_datetime is not None:
            return ReminderMode.ABSOLUTE

        normalized_mode = (explicit_mode or "").strip().lower()
        if normalized_mode in {mode.value for mode in ReminderMode}:
            return ReminderMode(normalized_mode)

        reference = (medical_time_reference or "").strip().lower()
        if "within" in reference:
            return ReminderMode.WINDOW
        if any(token in reference for token in ["after", "once", "when results"]):
            return ReminderMode.CONDITIONAL
        if reference:
            return ReminderMode.RELATIVE
        return ReminderMode.CONDITIONAL

    def _window_days(self, reminder: Reminder) -> int | None:
        if reminder.medical_window_start is None or reminder.medical_window_end is None:
            return None
        start = self._ensure_timezone(reminder.medical_window_start)
        end = self._ensure_timezone(reminder.medical_window_end)
        return max((end - start).days, 0)

    def _parse_iso_datetime(self, value: str | None) -> datetime | None:
        if not value or not str(value).strip():
            return None
        raw_value = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw_value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=self.timezone)
        return parsed.astimezone(self.timezone)

    def _extract_clock_time(self, text: str) -> time | None:
        match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2) or 0)
            meridiem = match.group(3)
            if meridiem == "pm" and hour != 12:
                hour += 12
            if meridiem == "am" and hour == 12:
                hour = 0
            return time(hour=hour, minute=minute)

        match_24 = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
        if match_24:
            return time(hour=int(match_24.group(1)), minute=int(match_24.group(2)))

        return None

    def _combine_date_time(self, value: datetime, clock: time) -> datetime:
        value = self._ensure_timezone(value)
        return value.replace(
            hour=clock.hour,
            minute=clock.minute,
            second=0,
            microsecond=0,
        )

    def _deduplicate_follow_up(self, follow_up: list) -> list:
        seen = set()
        unique = []
        for item in follow_up:
            if isinstance(item, dict):
                key = self._dedupe_key(
                    item.get("instruction_type") or item.get("type"),
                    item.get("doctor_instruction") or item.get("message") or item.get("when"),
                    item.get("source_text") or item.get("doctor_instruction"),
                )
            else:
                key = self._dedupe_key("follow_up", item, item)
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def _dedupe_key(self, instruction_type, doctor_instruction, source_text) -> tuple[str, str, str]:
        return (
            str(instruction_type or "").strip().lower(),
            str(doctor_instruction or "").strip().lower(),
            str(source_text or "").strip().lower(),
        )

    def _translate_for_patient(self, text: str, preferred_language: str | None) -> str:
        language = (preferred_language or "en").strip().lower()
        if language == "si":
            return self._get_translator().translate_to_sinhala(text)
        return text

    def _format_datetime(self, value: datetime | None) -> str:
        if value is None:
            return "an upcoming time"
        localized = self._ensure_timezone(value)
        return localized.strftime("%Y-%m-%d %I:%M %p")

    def _get_translator(self) -> TranslationService:
        if self._translator is None:
            self._translator = TranslationService()
        return self._translator

    def _weekday_index(self, weekday_name: str) -> int:
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        return weekdays[weekday_name]

    def _ensure_timezone(self, value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(self.timezone)
        if value.tzinfo is None:
            return value.replace(tzinfo=self.timezone)
        return value.astimezone(self.timezone)
