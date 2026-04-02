"""reminder preference flow

Revision ID: a4f9d6e8c123
Revises: d157c7b7457c
Create Date: 2026-04-02 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4f9d6e8c123"
down_revision: Union[str, None] = "d157c7b7457c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

reminderstatus = sa.Enum(
    "awaiting_patient_choice",
    "awaiting_schedule_choice",
    "declined",
    "scheduled",
    "completed",
    "cancelled",
    "failed",
    name="reminderstatus",
    native_enum=False,
)
remindermode = sa.Enum(
    "absolute",
    "relative",
    "window",
    "conditional",
    name="remindermode",
    native_enum=False,
)


def upgrade() -> None:
    op.execute("UPDATE reminders SET status = 'scheduled' WHERE status = 'pending'")
    op.execute("UPDATE reminders SET status = 'completed' WHERE status = 'sent'")

    with op.batch_alter_table("reminders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("instruction_type", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("doctor_instruction", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("medical_time_reference", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("medical_window_start", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("medical_window_end", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("exact_medical_datetime", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("patient_reminder_choice", sa.String(length=100), nullable=True))
        batch_op.add_column(
            sa.Column(
                "reminder_mode",
                remindermode,
                nullable=False,
                server_default="window",
            )
        )
        batch_op.add_column(sa.Column("source_text", sa.Text(), nullable=True))
        batch_op.alter_column("message", existing_type=sa.Text(), nullable=True)
        batch_op.alter_column("scheduled_at", existing_type=sa.DateTime(), nullable=True)
        batch_op.alter_column(
            "status",
            existing_type=sa.VARCHAR(length=20),
            type_=reminderstatus,
            existing_nullable=False,
        )


def downgrade() -> None:
    op.execute("UPDATE reminders SET status = 'failed' WHERE status = 'awaiting_patient_choice'")
    op.execute("UPDATE reminders SET status = 'failed' WHERE status = 'awaiting_schedule_choice'")
    op.execute("UPDATE reminders SET status = 'pending' WHERE status = 'scheduled'")
    op.execute("UPDATE reminders SET status = 'sent' WHERE status = 'completed'")
    op.execute("UPDATE reminders SET status = 'failed' WHERE status = 'declined'")
    op.execute("UPDATE reminders SET status = 'failed' WHERE status = 'cancelled'")

    with op.batch_alter_table("reminders", schema=None) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=reminderstatus,
            type_=sa.VARCHAR(length=20),
            existing_nullable=False,
        )
        batch_op.alter_column("scheduled_at", existing_type=sa.DateTime(), nullable=False)
        batch_op.alter_column("message", existing_type=sa.Text(), nullable=False)
        batch_op.drop_column("source_text")
        batch_op.drop_column("reminder_mode")
        batch_op.drop_column("patient_reminder_choice")
        batch_op.drop_column("exact_medical_datetime")
        batch_op.drop_column("medical_window_end")
        batch_op.drop_column("medical_window_start")
        batch_op.drop_column("medical_time_reference")
        batch_op.drop_column("doctor_instruction")
        batch_op.drop_column("instruction_type")
