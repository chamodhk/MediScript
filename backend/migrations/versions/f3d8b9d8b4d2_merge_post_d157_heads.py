"""merge post d157 heads

Revision ID: f3d8b9d8b4d2
Revises: a4f9d6e8c123, cafe245ac3d2
Create Date: 2026-04-03 09:30:00.000000

"""
from typing import Sequence, Union


revision: str = "f3d8b9d8b4d2"
down_revision: Union[str, Sequence[str], None] = ("a4f9d6e8c123", "cafe245ac3d2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
