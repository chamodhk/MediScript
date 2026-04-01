"""003_consultation_reminder_enums

Revision ID: 60eabfecebca
Revises: 23de54475b85
Create Date: 2026-03-29 17:25:07.064223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "60eabfecebca"
down_revision: Union[str, None] = "23de54475b85"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

consultationstatus = sa.Enum(
    "in_progress",
    "transcribed",
    "structured",
    "submitted",
    name="consultationstatus",
    native_enum=False,
)
remindertype = sa.Enum(
    "medication",
    "followup",
    "promo",
    name="remindertype",
    native_enum=False,
)
reminderstatus = sa.Enum(
    "pending",
    "sent",
    "failed",
    name="reminderstatus",
    native_enum=False,
)


def upgrade() -> None:
    with op.batch_alter_table("consultations", schema=None) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.VARCHAR(length=20),
            type_=consultationstatus,
            existing_nullable=False,
        )

    with op.batch_alter_table("reminders", schema=None) as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=sa.VARCHAR(length=20),
            type_=remindertype,
            existing_nullable=False,
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.VARCHAR(length=20),
            type_=reminderstatus,
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("reminders", schema=None) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=reminderstatus,
            type_=sa.VARCHAR(length=20),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "type",
            existing_type=remindertype,
            type_=sa.VARCHAR(length=20),
            existing_nullable=False,
        )

    with op.batch_alter_table("consultations", schema=None) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=consultationstatus,
            type_=sa.VARCHAR(length=20),
            existing_nullable=False,
        )
