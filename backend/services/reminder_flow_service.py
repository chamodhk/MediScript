from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.config import settings
from models.consultation import Consultation
from models.enums import ReminderMode, ReminderStatus, ReminderType
from models.patient import Patient
from models.reminder import Reminder
from services.command_router import CommandRouter, ParsedCommand
from services.message_formatter import MessageFormatter
from services.reminder_suggester import ReminderOption, ReminderSuggester
from services.translate_service import TranslationService
from services.twilio_service import send_whatsapp_message


STATE_ROOT = "flow:root"
STATE_INDIVIDUAL = "flow:individual"
STATE_OPTIONS_PREFIX = "flow:options:"


@dataclass(frozen=True)
class FlowResponse:
    message: str
    send_reply: bool = True


class ReminderFlowService:
    """Rule-based grouped reminder flow and command handling.

    Example:
        service = ReminderFlowService()
        await service.create_follow_up_flow(db, patient=patient, consultation=consultation, structured_data=data)
        response = await service.handle_incoming_message(db, from_number="+947...", body="/reminders")
    """

    def __init__(self) -> None:
        self.timezone = ZoneInfo(settings.REMINDER_TIMEZONE)
        self.command_router = CommandRouter()
        self.formatter = MessageFormatter()
        self.suggester = ReminderSuggester()
        self._translator: TranslationService | None = None

    async def create_follow_up_flow(
        self,
        db: AsyncSession,
        *,
        patient: Patient,
        consultation: Consultation,
        structured_data: dict | None,
    ) -> list[Reminder]:
        follow_up_items = structured_data.get("follow_up", []) if isinstance(structured_data, dict) else []
        if not follow_up_items:
            return []

        existing_result = await db.execute(
            select(Reminder).where(Reminder.consultation_id == consultation.id)
        )
        existing = existing_result.scalars().all()
        existing_keys = {
            self._dedupe_key(item.instruction_type, item.doctor_instruction, item.source_text)
            for item in existing
        }

        created: list[Reminder] = []
        for item in follow_up_items:
            reminder = self._build_reminder(patient.id, consultation.id, item)
            if reminder is None:
                continue
            key = self._dedupe_key(reminder.instruction_type, reminder.doctor_instruction, reminder.source_text)
            if key in existing_keys:
                continue
            db.add(reminder)
            created.append(reminder)
            existing_keys.add(key)

        if created:
            await db.commit()
            for reminder in created:
                await db.refresh(reminder)

        reminders = created or existing
        if reminders:
            self._send_message(
                patient.phone,
                self._translate(self.formatter.initial_flow_message(reminders), patient.preferred_language),
            )
        return created

    async def handle_incoming_message(
        self,
        db: AsyncSession,
        *,
        from_number: str,
        body: str,
    ) -> str:
        patient = await self._get_patient_by_phone(db, from_number)
        if patient is None:
            return "We could not find a patient record for this number."

        command = self.command_router.parse(body)
        if command is not None:
            return await self._handle_command(db, patient, command)

        consultation, reminders = await self._latest_consultation_context(db, patient.id)
        if consultation is None or not reminders:
            return "There are no reminder items for your recent consultations."

        state = self._conversation_state(reminders)
        normalized = (body or "").strip().lower()

        if state == STATE_ROOT:
            return await self._handle_root_choice(db, patient, reminders, normalized)

        if state == STATE_INDIVIDUAL:
            return await self._handle_individual_choice(db, patient, reminders, normalized)

        if state.startswith(STATE_OPTIONS_PREFIX):
            reminder_id = int(state.split(":")[-1])
            return await self._handle_option_choice(db, patient, reminders, reminder_id, normalized)

        return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

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
                self._send_message(reminder.patient.phone, reminder.message or self._final_message(reminder))
                reminder.sent_at = now
                sent_count += 1
                if reminder.patient_reminder_choice == "daily_until_done":
                    next_run = (now + timedelta(days=1)).replace(second=0, microsecond=0)
                    if reminder.medical_window_end and next_run > reminder.medical_window_end:
                        reminder.status = ReminderStatus.COMPLETED
                    else:
                        reminder.scheduled_at = next_run
                else:
                    reminder.status = ReminderStatus.SCHEDULED
            except Exception:
                reminder.status = ReminderStatus.FAILED

        if reminders:
            await db.commit()
        return sent_count

    async def _handle_command(
        self,
        db: AsyncSession,
        patient: Patient,
        command: ParsedCommand,
    ) -> str:
        consultation, reminders = await self._latest_consultation_context(db, patient.id)

        if command.name == "/help":
            return self._translate(self.formatter.help_message(), patient.preferred_language)

        if command.name == "/summary":
            instructions = []
            if consultation and isinstance(consultation.structured_output, dict):
                instructions = consultation.structured_output.get("instructions", [])
            return self._translate(
                self.formatter.summary_message(instructions, reminders),
                patient.preferred_language,
            )

        if command.name == "/followups":
            return self._translate(
                self.formatter.followups_message(reminders),
                patient.preferred_language,
            )

        if command.name == "/reminders":
            active = [item for item in reminders if item.status == ReminderStatus.SCHEDULED]
            return self._translate(
                self.formatter.reminders_message(active),
                patient.preferred_language,
            )

        if command.name == "/done":
            return await self._handle_done_command(db, patient, reminders, command.args)

        if command.name == "/stop":
            for reminder in reminders:
                if reminder.status in {
                    ReminderStatus.AWAITING_PATIENT_CHOICE,
                    ReminderStatus.AWAITING_SCHEDULE_CHOICE,
                    ReminderStatus.SCHEDULED,
                }:
                    reminder.status = ReminderStatus.CANCELLED
            await db.commit()
            return self._translate(self.formatter.stopped_message(), patient.preferred_language)

        if command.name == "/start":
            if consultation is None or not reminders:
                return "There is no recent follow-up flow to start."
            self._reset_flow(reminders)
            await db.commit()
            return self._translate(
                self.formatter.initial_flow_message(reminders),
                patient.preferred_language,
            )

        return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

    async def _handle_done_command(
        self,
        db: AsyncSession,
        patient: Patient,
        reminders: list[Reminder],
        args: list[str],
    ) -> str:
        scheduled = [item for item in reminders if item.status == ReminderStatus.SCHEDULED]
        if not scheduled:
            return self._translate(
                "There are no scheduled reminders to mark as done.",
                patient.preferred_language,
            )

        if not args:
            return self._translate(
                self.formatter.ask_done_which_message(scheduled),
                patient.preferred_language,
            )

        if not args[0].isdigit():
            return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

        index = int(args[0]) - 1
        if index < 0 or index >= len(scheduled):
            return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

        scheduled[index].status = ReminderStatus.COMPLETED
        await db.commit()
        return self._translate("Marked as completed.", patient.preferred_language)

    async def _handle_root_choice(
        self,
        db: AsyncSession,
        patient: Patient,
        reminders: list[Reminder],
        normalized: str,
    ) -> str:
        if normalized == "1":
            return await self._confirm_suggested(db, patient, reminders)
        if normalized == "2":
            for reminder in reminders:
                if self.suggester.is_eligible(reminder):
                    reminder.status = ReminderStatus.AWAITING_SCHEDULE_CHOICE
                    reminder.patient_reminder_choice = STATE_INDIVIDUAL
            await db.commit()
            return self._translate(
                self.formatter.individual_selection_message(reminders),
                patient.preferred_language,
            )
        if normalized == "3":
            for reminder in reminders:
                reminder.status = ReminderStatus.DECLINED
                reminder.patient_reminder_choice = "declined"
            await db.commit()
            return self._translate(self.formatter.no_reminders_message(), patient.preferred_language)

        return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

    async def _confirm_suggested(
        self,
        db: AsyncSession,
        patient: Patient,
        reminders: list[Reminder],
    ) -> str:
        scheduled: list[Reminder] = []
        for reminder in reminders:
            if not self.suggester.is_eligible(reminder):
                reminder.status = ReminderStatus.CANCELLED
                reminder.patient_reminder_choice = "alert_only"
                continue
            suggestion = self.suggester.suggested_option(reminder)
            if suggestion is None:
                continue
            reminder.patient_reminder_choice = suggestion.key
            reminder.scheduled_at = self.suggester.resolve_option(reminder, suggestion.key).replace(tzinfo=None)
            reminder.message = self._translate(self._final_message(reminder), patient.preferred_language)
            reminder.status = ReminderStatus.SCHEDULED
            scheduled.append(reminder)
        await db.commit()
        return self._translate(
            self.formatter.reminders_message(scheduled) if scheduled else self.formatter.no_reminders_message(),
            patient.preferred_language,
        )

    async def _handle_individual_choice(
        self,
        db: AsyncSession,
        patient: Patient,
        reminders: list[Reminder],
        normalized: str,
    ) -> str:
        eligible = [item for item in reminders if self.suggester.is_eligible(item)]
        if not normalized.isdigit():
            return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

        index = int(normalized) - 1
        if index < 0 or index >= len(eligible):
            return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

        selected = eligible[index]
        options = self.suggester.options_for(selected)
        if selected.reminder_mode == ReminderMode.RELATIVE:
            default = self.suggester.suggested_option(selected)
            if default is None:
                return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)
            selected.patient_reminder_choice = default.key
            selected.scheduled_at = self.suggester.resolve_option(selected, default.key).replace(tzinfo=None)
            selected.message = self._translate(self._final_message(selected), patient.preferred_language)
            selected.status = ReminderStatus.SCHEDULED
            await db.commit()
            return self._translate(self.formatter.confirmation_message(selected), patient.preferred_language)

        selected.patient_reminder_choice = f"{STATE_OPTIONS_PREFIX}{selected.id}"
        await db.commit()
        return self._translate(
            self.formatter.options_message(selected, [option.label for option in options]),
            patient.preferred_language,
        )

    async def _handle_option_choice(
        self,
        db: AsyncSession,
        patient: Patient,
        reminders: list[Reminder],
        reminder_id: int,
        normalized: str,
    ) -> str:
        selected = next((item for item in reminders if item.id == reminder_id), None)
        if selected is None:
            return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)
        if not normalized.isdigit():
            return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

        options = self.suggester.options_for(selected)
        index = int(normalized) - 1
        if index < 0 or index >= len(options):
            return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

        chosen = options[index]
        scheduled_at = self.suggester.resolve_option(selected, chosen.key)
        if scheduled_at is None:
            return self._translate(self.formatter.invalid_choice_message(), patient.preferred_language)

        selected.patient_reminder_choice = chosen.key
        selected.scheduled_at = scheduled_at.replace(tzinfo=None)
        selected.message = self._translate(self._final_message(selected), patient.preferred_language)
        selected.status = ReminderStatus.SCHEDULED
        await db.commit()
        return self._translate(self.formatter.confirmation_message(selected), patient.preferred_language)

    async def _latest_consultation_context(
        self,
        db: AsyncSession,
        patient_id: int,
    ) -> tuple[Consultation | None, list[Reminder]]:
        consultation_result = await db.execute(
            select(Consultation)
            .where(Consultation.patient_id == patient_id)
            .order_by(Consultation.created_at.desc())
        )
        consultation = consultation_result.scalars().first()

        if consultation is None:
            return None, []

        reminder_result = await db.execute(
            select(Reminder)
            .where(
                Reminder.patient_id == patient_id,
                Reminder.consultation_id == consultation.id,
                Reminder.type == ReminderType.FOLLOWUP,
            )
            .order_by(Reminder.id.asc())
        )
        return consultation, reminder_result.scalars().all()

    async def _get_patient_by_phone(self, db: AsyncSession, phone: str) -> Patient | None:
        result = await db.execute(select(Patient).where(Patient.phone == phone))
        return result.scalar_one_or_none()

    def _conversation_state(self, reminders: list[Reminder]) -> str:
        for reminder in reminders:
            if reminder.patient_reminder_choice and reminder.patient_reminder_choice.startswith(STATE_OPTIONS_PREFIX):
                return reminder.patient_reminder_choice
        if any(
            reminder.status == ReminderStatus.AWAITING_SCHEDULE_CHOICE
            and reminder.patient_reminder_choice == STATE_INDIVIDUAL
            for reminder in reminders
        ):
            return STATE_INDIVIDUAL
        if any(reminder.status == ReminderStatus.AWAITING_PATIENT_CHOICE for reminder in reminders):
            return STATE_ROOT
        return "idle"

    def _reset_flow(self, reminders: list[Reminder]) -> None:
        for reminder in reminders:
            if reminder.status in {
                ReminderStatus.DECLINED,
                ReminderStatus.CANCELLED,
                ReminderStatus.AWAITING_SCHEDULE_CHOICE,
            }:
                reminder.status = ReminderStatus.AWAITING_PATIENT_CHOICE
                reminder.patient_reminder_choice = STATE_ROOT

    def _build_reminder(self, patient_id: int, consultation_id: int, item: dict | str) -> Reminder | None:
        normalized = self._normalize_follow_up_item(item)
        if not normalized["doctor_instruction"]:
            return None
        return Reminder(
            patient_id=patient_id,
            consultation_id=consultation_id,
            message=None,
            instruction_type=normalized["instruction_type"],
            doctor_instruction=normalized["doctor_instruction"],
            medical_time_reference=normalized["medical_time_reference"],
            medical_window_start=normalized["medical_window_start"],
            medical_window_end=normalized["medical_window_end"],
            exact_medical_datetime=normalized["exact_medical_datetime"],
            patient_reminder_choice=STATE_ROOT,
            reminder_mode=normalized["reminder_mode"],
            source_text=normalized["source_text"],
            scheduled_at=None,
            sent_at=None,
            type=ReminderType.FOLLOWUP,
            status=ReminderStatus.AWAITING_PATIENT_CHOICE,
        )

    def _normalize_follow_up_item(self, item: dict | str) -> dict:
        if isinstance(item, dict):
            instruction_type = str(item.get("instruction_type") or item.get("type") or "follow_up").strip()
            doctor_instruction = str(item.get("doctor_instruction") or item.get("source_text") or "").strip()
            medical_time_reference = str(item.get("medical_time_reference") or "").strip() or None
            exact = self._parse_iso_datetime(item.get("exact_medical_datetime"))
            window_start = self._parse_iso_datetime(item.get("medical_window_start"))
            window_end = self._parse_iso_datetime(item.get("medical_window_end"))
            mode = self._parse_mode(item.get("reminder_mode"), exact, medical_time_reference)
            source_text = str(item.get("source_text") or doctor_instruction).strip() or None
        else:
            instruction_type = "follow_up"
            doctor_instruction = str(item).strip()
            medical_time_reference = None
            exact = None
            window_start = None
            window_end = None
            mode = ReminderMode.RELATIVE
            source_text = doctor_instruction

        if window_start is None and window_end is None and medical_time_reference:
            window_start, window_end = self._derive_window(medical_time_reference)

        return {
            "instruction_type": instruction_type,
            "doctor_instruction": doctor_instruction,
            "medical_time_reference": medical_time_reference,
            "exact_medical_datetime": exact,
            "medical_window_start": window_start,
            "medical_window_end": window_end,
            "reminder_mode": mode,
            "source_text": source_text,
        }

    def _derive_window(self, reference: str) -> tuple[datetime | None, datetime | None]:
        text = reference.lower()
        now = datetime.now(self.timezone)
        match = re.search(r"within\s+(\d+)\s+(day|days|week|weeks)", text)
        if not match:
            return None, None
        amount = int(match.group(1))
        unit = match.group(2)
        if "week" in unit:
            delta = timedelta(weeks=amount)
        else:
            delta = timedelta(days=amount)
        return now, now + delta

    def _parse_mode(
        self,
        value: str | None,
        exact: datetime | None,
        medical_time_reference: str | None,
    ) -> ReminderMode:
        if exact is not None:
            return ReminderMode.ABSOLUTE
        normalized = (value or "").strip().lower()
        if normalized in {mode.value for mode in ReminderMode}:
            return ReminderMode(normalized)
        if medical_time_reference and "within" in medical_time_reference.lower():
            return ReminderMode.WINDOW
        if medical_time_reference:
            return ReminderMode.RELATIVE
        return ReminderMode.CONDITIONAL

    def _parse_iso_datetime(self, value) -> datetime | None:
        if not value:
            return None
        raw = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=self.timezone)
        return parsed.astimezone(self.timezone)

    def _dedupe_key(self, instruction_type, doctor_instruction, source_text) -> tuple[str, str, str]:
        return (
            str(instruction_type or "").strip().lower(),
            str(doctor_instruction or "").strip().lower(),
            str(source_text or "").strip().lower(),
        )

    def _final_message(self, reminder: Reminder) -> str:
        if reminder.medical_time_reference:
            return f"Reminder: {reminder.doctor_instruction}. Timeframe: {reminder.medical_time_reference}."
        return f"Reminder: {reminder.doctor_instruction}."

    def _translate(self, text: str, preferred_language: str | None) -> str:
        language = (preferred_language or "en").strip().lower()
        if language == "si":
            return self._translator_instance().translate_to_sinhala(text)
        return text

    def _translator_instance(self) -> TranslationService:
        if self._translator is None:
            self._translator = TranslationService()
        return self._translator

    def _send_message(self, to_number: str, message_body: str) -> None:
        send_whatsapp_message(to_number=to_number, message_body=message_body)
