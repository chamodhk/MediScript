from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from core.config import settings
from models.enums import ReminderMode
from models.reminder import Reminder


@dataclass(frozen=True)
class ReminderOption:
    key: str
    label: str


class ReminderSuggester:
    """Pure rule-based reminder suggestions and time resolution.

    Example:
        suggester = ReminderSuggester()
        options = suggester.options_for(reminder)
    """

    def __init__(self) -> None:
        self.timezone = ZoneInfo(settings.REMINDER_TIMEZONE)

    def is_eligible(self, reminder: Reminder) -> bool:
        return reminder.reminder_mode != ReminderMode.CONDITIONAL

    def suggested_option(self, reminder: Reminder) -> ReminderOption | None:
        if not self.is_eligible(reminder):
            return None
        if reminder.reminder_mode == ReminderMode.ABSOLUTE:
            return ReminderOption("morning_of", "Morning of the appointment")
        if reminder.reminder_mode == ReminderMode.RELATIVE:
            return ReminderOption("default_relative", "Suggested reminder")
        if reminder.reminder_mode == ReminderMode.WINDOW:
            return ReminderOption("middle_of_window", "Suggested reminder")
        return ReminderOption("tomorrow_morning", "Tomorrow morning")

    def options_for(self, reminder: Reminder) -> list[ReminderOption]:
        if reminder.reminder_mode == ReminderMode.ABSOLUTE:
            return [
                ReminderOption("morning_of", "Morning of the appointment"),
                ReminderOption("two_hours_before", "2 hours before"),
                ReminderOption("at_time", "At the appointment time"),
            ]

        if reminder.reminder_mode == ReminderMode.WINDOW:
            window_days = self._window_days(reminder)
            if window_days is not None and window_days <= 3:
                return [
                    ReminderOption("tomorrow_morning", "Tomorrow morning"),
                    ReminderOption("tomorrow_evening", "Tomorrow evening"),
                    ReminderOption("middle_of_window", "The middle of the timeframe"),
                    ReminderOption("daily_until_done", "Daily until done"),
                ]
            return [
                ReminderOption("in_3_days", "In 3 days"),
                ReminderOption("in_5_days", "In 5 days"),
                ReminderOption("last_day_morning", "On the last day"),
                ReminderOption("daily_until_done", "Daily until done"),
            ]

        if reminder.reminder_mode == ReminderMode.RELATIVE:
            return [
                ReminderOption("default_relative", "Suggested reminder"),
                ReminderOption("tomorrow_morning", "Tomorrow morning"),
                ReminderOption("in_3_days", "In 3 days"),
                ReminderOption("daily_until_done", "Daily until done"),
            ]

        return []

    def resolve_option(self, reminder: Reminder, option_key: str) -> datetime | None:
        now = datetime.now(self.timezone).replace(second=0, microsecond=0)
        exact = self._localized(reminder.exact_medical_datetime)
        window_start = self._localized(reminder.medical_window_start)
        window_end = self._localized(reminder.medical_window_end)

        if option_key == "morning_of" and exact is not None:
            return exact.replace(hour=8, minute=0, second=0, microsecond=0)
        if option_key == "two_hours_before" and exact is not None:
            return exact - timedelta(hours=2)
        if option_key == "at_time" and exact is not None:
            return exact
        if option_key == "default_relative":
            if exact is not None:
                return exact - timedelta(hours=2)
            if window_start is not None:
                return window_start.replace(hour=9, minute=0, second=0, microsecond=0)
            return (now + timedelta(days=1)).replace(hour=9, minute=0)
        if option_key == "middle_of_window":
            if window_start is None or window_end is None:
                return (now + timedelta(days=1)).replace(hour=9, minute=0)
            midpoint = window_start + (window_end - window_start) / 2
            return midpoint.replace(hour=9, minute=0, second=0, microsecond=0)
        if option_key == "last_day_morning":
            if window_end is None:
                return None
            return window_end.replace(hour=9, minute=0, second=0, microsecond=0)
        if option_key == "tomorrow_morning":
            return self._combine(now + timedelta(days=1), time(hour=9))
        if option_key == "tomorrow_evening":
            return self._combine(now + timedelta(days=1), time(hour=18))
        if option_key == "in_3_days":
            return self._combine(now + timedelta(days=3), time(hour=9))
        if option_key == "in_5_days":
            return self._combine(now + timedelta(days=5), time(hour=9))
        if option_key == "daily_until_done":
            return self._combine(now + timedelta(days=1), time(hour=9))
        return None

    def _window_days(self, reminder: Reminder) -> int | None:
        start = self._localized(reminder.medical_window_start)
        end = self._localized(reminder.medical_window_end)
        if start is None or end is None:
            return None
        return max((end - start).days, 0)

    def _combine(self, value: datetime, clock: time) -> datetime:
        localized = self._localized(value) or datetime.now(self.timezone)
        return localized.replace(hour=clock.hour, minute=clock.minute, second=0, microsecond=0)

    def _localized(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=self.timezone)
        return value.astimezone(self.timezone)
