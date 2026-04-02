from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import settings
from core.database import AsyncSessionLocal
from services.reminder_flow_service import ReminderFlowService


class SchedulerService:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone=settings.REMINDER_TIMEZONE)
        self.reminder_service = ReminderFlowService()
        self._started = False

    def start(self) -> None:
        if self._started:
            return

        self.scheduler.add_job(
            self._process_due_reminders,
            trigger="interval",
            seconds=settings.REMINDER_POLL_SECONDS,
            id="process_due_reminders",
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.start()
        self._started = True

    def shutdown(self) -> None:
        if not self._started:
            return

        self.scheduler.shutdown(wait=False)
        self._started = False

    async def _process_due_reminders(self) -> None:
        async with AsyncSessionLocal() as session:
            await self.reminder_service.send_due_reminders(session)


scheduler_service = SchedulerService()
