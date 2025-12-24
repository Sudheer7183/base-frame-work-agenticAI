"""add_invitation_fields

Revision ID: cc968bca1084
Revises: 4d9384a7e82e
Create Date: 2025-12-24 06:38:17.163373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cc968bca1084'
down_revision: Union[str, None] = '4d9384a7e82e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add invitation-related fields to users table for SSO email invitation workflow.
    This migration only runs on tenant schemas, not public.
    """
    
    # Get the target schema from context
    schema = context.get_context().version_table_schema
    
    # Skip if running on public schema
    if not schema or schema == "public":
        print(f"[Migration] Skipping - this migration is only for tenant schemas")
        return
    
    print(f"[Migration] Adding invitation fields to users table in schema: {schema}")
    
    # Verify we're in the right schema
    conn = op.get_bind()
    result = conn.execute(sa.text("SHOW search_path"))
    current_path = result.scalar()
    print(f"[Migration] Current search_path: {current_path}")
    
    # -------------------------------
    # Add invitation fields
    # -------------------------------
    
    # invitation_status - tracks the invitation lifecycle
    op.add_column(
        'users',
        sa.Column(
            'invitation_status',
            sa.String(20),
            nullable=True,
            server_default='accepted',
            comment='Invitation status: pending, accepted, expired, cancelled'
        ),
        schema=schema
    )
    
    # invitation_token - secure token for invitation acceptance
    op.add_column(
        'users',
        sa.Column(
            'invitation_token',
            sa.String(255),
            nullable=True,
            comment='Secure token for invitation acceptance'
        ),
        schema=schema
    )
    
    # invited_by - references the admin user who sent the invitation
    op.add_column(
        'users',
        sa.Column(
            'invited_by',
            sa.Integer(),
            nullable=True,
            comment='User ID who sent the invitation'
        ),
        schema=schema
    )
    
    # invited_at - timestamp when invitation was sent
    op.add_column(
        'users',
        sa.Column(
            'invited_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When invitation was sent'
        ),
        schema=schema
    )
    
    # accepted_at - timestamp when invitation was accepted
    op.add_column(
        'users',
        sa.Column(
            'accepted_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When invitation was accepted'
        ),
        schema=schema
    )
    
    # invitation_expires_at - when the invitation expires
    op.add_column(
        'users',
        sa.Column(
            'invitation_expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When invitation expires'
        ),
        schema=schema
    )
    
    # provisioning_method - how the user was created
    op.add_column(
        'users',
        sa.Column(
            'provisioning_method',
            sa.String(50),
            nullable=True,
            server_default='manual',
            comment='How user was created: manual, invitation, jit_sso, directory_sync'
        ),
        schema=schema
    )
    
    # -------------------------------
    # Add foreign key constraint
    # -------------------------------
    
    op.create_foreign_key(
        'fk_users_invited_by',
        'users',
        'users',
        ['invited_by'],
        ['id'],
        source_schema=schema,
        referent_schema=schema,
        ondelete='SET NULL'
    )
    
    # -------------------------------
    # Add indexes for performance
    # -------------------------------
    
    # Index for invitation token lookups (partial index - only when token exists)
    op.create_index(
        'idx_users_invitation_token',
        'users',
        ['invitation_token'],
        unique=False,
        schema=schema,
        postgresql_where=sa.text('invitation_token IS NOT NULL')
    )
    
    # Index for pending invitation queries (partial index - only pending status)
    op.create_index(
        'idx_users_invitation_status',
        'users',
        ['invitation_status'],
        unique=False,
        schema=schema,
        postgresql_where=sa.text("invitation_status = 'pending'")
    )
    
    print(f"[Migration] ✓ Successfully added invitation fields to users table in {schema}")



def downgrade() -> None:
    """
    Remove invitation-related fields from users table.
    """
    
    # Get the target schema from context
    schema = context.get_context().version_table_schema
    
    # Skip if running on public schema
    if not schema or schema == "public":
        print(f"[Migration] Skipping - this migration is only for tenant schemas")
        return
    
    print(f"[Migration] Removing invitation fields from users table in schema: {schema}")
    
    # -------------------------------
    # Drop indexes first
    # -------------------------------
    
    op.drop_index('idx_users_invitation_status', table_name='users', schema=schema)
    op.drop_index('idx_users_invitation_token', table_name='users', schema=schema)
    
    # -------------------------------
    # Drop foreign key constraint
    # -------------------------------
    
    op.drop_constraint('fk_users_invited_by', 'users', type_='foreignkey', schema=schema)
    
    # -------------------------------
    # Drop columns
    # -------------------------------
    
    op.drop_column('users', 'provisioning_method', schema=schema)
    op.drop_column('users', 'invitation_expires_at', schema=schema)
    op.drop_column('users', 'accepted_at', schema=schema)
    op.drop_column('users', 'invited_at', schema=schema)
    op.drop_column('users', 'invited_by', schema=schema)
    op.drop_column('users', 'invitation_token', schema=schema)
    op.drop_column('users', 'invitation_status', schema=schema)
    
    print(f"[Migration] ✓ Successfully removed invitation fields from users table in {schema}")



