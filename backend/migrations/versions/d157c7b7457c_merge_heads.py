"""merge heads

Revision ID: d157c7b7457c
Revises: 60eabfecebca, db9c17b86d8d
Create Date: 2026-03-30 18:47:39.186327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd157c7b7457c'
down_revision: Union[str, None] = ('60eabfecebca', 'db9c17b86d8d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
