from __future__ import annotations

from datetime import datetime

from models.enums import ReminderMode, ReminderStatus
from models.reminder import Reminder


class MessageFormatter:
    """Human-friendly WhatsApp text templates.

    Example:
        formatter = MessageFormatter()
        text = formatter.help_message()
    """

    def initial_flow_message(self, reminders: list[Reminder]) -> str:
        follow_up_lines = self._follow_up_lines(reminders, numbered=True, eligible_only=False)
        lines = [
            "Your doctor mentioned these next steps:",
            *follow_up_lines,
            "",
            "How would you like to handle reminders?",
            "1 = Use the suggested reminders",
            "2 = Choose reminders individually",
            "3 = No reminders",
        ]
        return "\n".join(lines)

    def individual_selection_message(self, reminders: list[Reminder]) -> str:
        eligible = [reminder for reminder in reminders if reminder.reminder_mode != ReminderMode.CONDITIONAL]
        lines = [
            "Choose the item you want a reminder for:",
            *self._follow_up_lines(eligible, numbered=True, eligible_only=True),
            "",
            "Reply with one number at a time.",
        ]
        conditional_count = len(reminders) - len(eligible)
        if conditional_count:
            lines.append("Alert-only items are shown in /followups but cannot be scheduled.")
        return "\n".join(lines)

    def options_message(self, reminder: Reminder, option_labels: list[str]) -> str:
        lines = [
            f"When would you like to be reminded about: {reminder.doctor_instruction}?",
        ]
        for index, label in enumerate(option_labels, start=1):
            lines.append(f"{index} = {label}")
        return "\n".join(lines)

    def confirmation_message(self, reminder: Reminder) -> str:
        if reminder.patient_reminder_choice == "daily_until_done":
            return (
                f"Okay. We will remind you daily about: {reminder.doctor_instruction}. "
                "Reply /done when you have completed it."
            )
        return (
            f"Reminder set for {self._format_datetime(reminder.scheduled_at)} "
            f"for: {reminder.doctor_instruction}."
        )

    def reminders_message(self, reminders: list[Reminder]) -> str:
        if not reminders:
            return "You do not have any active reminders right now."

        lines = ["Your active reminders:"]
        for index, reminder in enumerate(reminders, start=1):
            status_label = reminder.status.value.replace("_", " ")
            when = self._format_datetime(reminder.scheduled_at)
            lines.append(f"{index}. {reminder.doctor_instruction} [{status_label}] {when}")
        return "\n".join(lines)

    def followups_message(self, reminders: list[Reminder]) -> str:
        if not reminders:
            return "No follow-up items were found for your latest consultation."
        lines = ["Follow-up items from your latest consultation:"]
        lines.extend(self._follow_up_lines(reminders, numbered=True, eligible_only=False))
        return "\n".join(lines)

    def summary_message(self, instructions: list[str], reminders: list[Reminder]) -> str:
        lines = ["Consultation summary:"]
        if instructions:
            lines.append("Instructions:")
            lines.extend(f"- {item}" for item in instructions)
        if reminders:
            lines.append("Follow-up:")
            lines.extend(self._follow_up_lines(reminders, numbered=False, eligible_only=False))
        return "\n".join(lines)

    def help_message(self) -> str:
        return "\n".join(
            [
                "Available commands:",
                "/help",
                "/summary",
                "/followups",
                "/reminders",
                "/done",
                "/done 1",
                "/stop",
                "/start",
            ]
        )

    def ask_done_which_message(self, reminders: list[Reminder]) -> str:
        if not reminders:
            return "There are no active reminders to mark as done."
        lines = ["Which reminder did you complete?"]
        for index, reminder in enumerate(reminders, start=1):
            lines.append(f"{index}. {reminder.doctor_instruction}")
        lines.append("Reply with /done 1, /done 2, and so on.")
        return "\n".join(lines)

    def no_reminders_message(self) -> str:
        return "Okay, we will not send reminders for these follow-up items."

    def stopped_message(self) -> str:
        return "All active reminder conversations have been stopped."

    def restarted_message(self) -> str:
        return "Restarting the reminder setup for your latest consultation."

    def invalid_choice_message(self) -> str:
        return "I did not understand that. Reply with one of the numbers shown, or use /help."

    def alert_only_note(self, reminder: Reminder) -> str:
        return f"{reminder.doctor_instruction} (alert only)"

    def _follow_up_lines(
        self,
        reminders: list[Reminder],
        *,
        numbered: bool,
        eligible_only: bool,
    ) -> list[str]:
        lines: list[str] = []
        filtered = reminders
        if eligible_only:
            filtered = [reminder for reminder in reminders if reminder.reminder_mode != ReminderMode.CONDITIONAL]
        for index, reminder in enumerate(filtered, start=1):
            prefix = f"{index}. " if numbered else "- "
            suffix = ""
            if reminder.reminder_mode == ReminderMode.CONDITIONAL:
                suffix = " (alert only)"
            elif reminder.medical_time_reference:
                suffix = f" [{reminder.medical_time_reference}]"
            lines.append(f"{prefix}{reminder.doctor_instruction}{suffix}")
        return lines

    def _format_datetime(self, value: datetime | None) -> str:
        if value is None:
            return ""
        return value.strftime("%Y-%m-%d %I:%M %p")
