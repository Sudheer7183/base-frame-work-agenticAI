"""add_audit_logs_table

Revision ID: 14eb31fb242b
Revises: a93ad6fadec3
Create Date: <auto_generated>
"""
from typing import Sequence, Union
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '14eb31fb242b'
down_revision: Union[str, None] = 'a93ad6fadec3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the target schema from context
    schema = context.get_context().version_table_schema
    
    # IMPORTANT: This table should ONLY be created in PUBLIC schema
    # Skip if running on tenant schemas
    if schema and schema != "public":
        print(f"[Migration] Skipping audit_logs - this is a public schema table only")
        return
    
    print(f"[Migration] Creating audit_logs table in public schema")
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'audit_logs' in inspector.get_table_names(schema='public'):
        print(f"[Migration {revision}] Table already exists, skipping")
        return

    # Create audit_logs table in public schema
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

    # pass

def downgrade() -> None:
    # Get the target schema from context
    schema = context.get_context().version_table_schema
    
    # Only drop from public schema
    if schema and schema != "public":
        return
        
    op.drop_table('audit_logs', schema='public')

    # pass