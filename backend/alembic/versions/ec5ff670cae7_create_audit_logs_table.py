"""create audit_logs table

Revision ID: ec5ff670cae7
Revises: 14eb31fb242b
Create Date: 2025-12-22 13:00:44.970390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ec5ff670cae7'
down_revision: Union[str, None] = '14eb31fb242b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    # Create indexes
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'], schema='public')
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'], schema='public')
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'], schema='public')
    op.create_index('idx_audit_user_action', 'audit_logs', ['user_id', 'action'], schema='public')
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'], schema='public')
    op.create_index('idx_audit_timestamp_action', 'audit_logs', ['timestamp', 'action'], schema='public')



def downgrade() -> None:
    op.drop_table('audit_logs', schema='public')
