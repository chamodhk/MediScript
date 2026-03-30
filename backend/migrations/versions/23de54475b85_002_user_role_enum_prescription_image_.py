"""002_user_role_enum_prescription_image_blob

Revision ID: 23de54475b85
Revises: 3ea0854ac8ee
Create Date: 2026-03-29 17:21:08.513878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23de54475b85'
down_revision: Union[str, None] = '3ea0854ac8ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

userrole_enum = sa.Enum('admin', 'doctor', 'pharmacist', name='userrole', native_enum=False)


def upgrade() -> None:
    op.add_column('prescriptions', sa.Column('image_data', sa.LargeBinary(), nullable=True))
    op.add_column(
        'prescriptions',
        sa.Column(
            'image_mime_type',
            sa.String(length=64),
            nullable=False,
            server_default='image/png',
        ),
    )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'role',
            existing_type=sa.VARCHAR(length=20),
            type_=userrole_enum,
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'role',
            existing_type=userrole_enum,
            type_=sa.VARCHAR(length=20),
            existing_nullable=False,
        )

    op.drop_column('prescriptions', 'image_mime_type')
    op.drop_column('prescriptions', 'image_data')
