"""
Initial database schema with agents, HITL, and users tables.

Revision ID: 001_init
Revises: 
Create Date: 2024-12-16 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial tables with proper indexes and constraints."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('keycloak_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('roles', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('keycloak_id', name='uq_users_keycloak_id'),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    
    # Create indexes for users table
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_keycloak_id', 'users', ['keycloak_id'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('workflow', sa.String(length=255), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_agents_name'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL')
    )
    
    # Create indexes for agents table
    op.create_index('idx_agents_name', 'agents', ['name'])
    op.create_index('idx_agents_active', 'agents', ['active'])
    op.create_index('idx_agents_workflow', 'agents', ['workflow'])
    op.create_index('idx_agents_created_by', 'agents', ['created_by'])
    
    # Create HITL records table
    op.create_table(
        'hitl_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('agent_name', sa.String(length=255), nullable=False),
        sa.Column('execution_id', sa.String(length=255), nullable=True),
        sa.Column('input', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('output', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('feedback', postgresql.JSONB(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timeout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'timeout', 'escalated')", 
                          name='ck_hitl_status'),
        sa.CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')",
                          name='ck_hitl_priority')
    )
    
    # Create indexes for HITL records table
    op.create_index('idx_hitl_agent_id', 'hitl_records', ['agent_id'])
    op.create_index('idx_hitl_status', 'hitl_records', ['status'])
    op.create_index('idx_hitl_priority', 'hitl_records', ['priority'])
    op.create_index('idx_hitl_assigned_to', 'hitl_records', ['assigned_to'])
    op.create_index('idx_hitl_reviewed_by', 'hitl_records', ['reviewed_by'])
    op.create_index('idx_hitl_created_at', 'hitl_records', ['created_at'])
    op.create_index('idx_hitl_execution_id', 'hitl_records', ['execution_id'])
    op.create_index('idx_hitl_escalated', 'hitl_records', ['escalated'])
    
    # Create composite indexes for common queries
    op.create_index('idx_hitl_status_priority', 'hitl_records', ['status', 'priority'])
    op.create_index('idx_hitl_agent_status', 'hitl_records', ['agent_id', 'status'])
    
    # Create agent execution logs table for audit
    op.create_table(
        'agent_execution_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('input', postgresql.JSONB(), nullable=True),
        sa.Column('output', postgresql.JSONB(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('started_by', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['started_by'], ['users.id'], ondelete='SET NULL')
    )
    
    # Create indexes for execution logs
    op.create_index('idx_exec_logs_agent_id', 'agent_execution_logs', ['agent_id'])
    op.create_index('idx_exec_logs_execution_id', 'agent_execution_logs', ['execution_id'])
    op.create_index('idx_exec_logs_status', 'agent_execution_logs', ['status'])
    op.create_index('idx_exec_logs_started_at', 'agent_execution_logs', ['started_at'])


def downgrade():
    """Drop all tables in reverse order."""
    op.drop_table('agent_execution_logs')
    op.drop_table('hitl_records')
    op.drop_table('agents')
    op.drop_table('users')