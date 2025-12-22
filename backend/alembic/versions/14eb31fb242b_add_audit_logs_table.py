"""add_audit_logs_table

Revision ID: 14eb31fb242b
Revises: a93ad6fadec3
Create Date: 2025-12-22 11:35:45.477726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14eb31fb242b'
down_revision: Union[str, None] = 'a93ad6fadec3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
