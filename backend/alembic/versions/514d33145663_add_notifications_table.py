"""add_notifications_table

Revision ID: 514d33145663
Revises: ec5ff670cae7
Create Date: 2025-12-22 13:03:47.177996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '514d33145663'
down_revision: Union[str, None] = 'ec5ff670cae7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', postgresql.JSONB(), nullable=True),
        sa.Column('priority', sa.String(20), nullable=False, server_default='normal'),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('channels', postgresql.JSONB(), nullable=True),
        sa.Column('delivered_channels', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    # Create indexes
    op.create_index('idx_notification_user_id', 'notifications', ['user_id'], schema='public')
    op.create_index('idx_notification_user_unread', 'notifications', ['user_id', 'read'], schema='public')
    op.create_index('idx_notification_created_at', 'notifications', ['created_at'], schema='public')


def downgrade() -> None:
    op.drop_table('notifications', schema='public')
