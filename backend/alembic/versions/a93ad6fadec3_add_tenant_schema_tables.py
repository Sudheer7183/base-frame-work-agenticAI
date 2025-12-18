# """
# add_tenant_schema_tables

# Revision ID: a93ad6fadec3
# Revises: c1d684656a7d
# Create Date: 2025-12-17
# """

# from typing import Sequence, Union

# from alembic import op, context
# import sqlalchemy as sa
# from sqlalchemy.dialects import postgresql

# # revision identifiers, used by Alembic.
# revision: str = "a93ad6fadec3"
# down_revision: Union[str, None] = "c1d684656a7d"
# branch_labels: Union[str, Sequence[str], None] = None
# depends_on: Union[str, Sequence[str], None] = None


# def upgrade() -> None:
#     """
#     Create tenant-specific tables inside the tenant schema.
#     """

#     # 🔑 Get schema passed from env.py
#     schema = context.get_context().version_table_schema or "public"
#     print("schema name from migration file",schema)
#     if not schema:
#         raise RuntimeError(
#             "Tenant schema not set. "
#             "This migration must be run with alembic_cfg.set_main_option('schema', <tenant_schema>)."
#         )

#     # -------------------------------
#     # USERS TABLE
#     # -------------------------------
#     op.create_table(
#         "users",
#         sa.Column("id", sa.Integer(), nullable=False),
#         sa.Column("keycloak_id", sa.String(255), nullable=True),
#         sa.Column("email", sa.String(255), nullable=False),
#         sa.Column("username", sa.String(255), nullable=True),
#         sa.Column("hashed_password", sa.String(255), nullable=True),
#         sa.Column("full_name", sa.String(255), nullable=True),
#         sa.Column("avatar_url", sa.String(500), nullable=True),
#         sa.Column("phone", sa.String(50), nullable=True),

#         sa.Column(
#             "roles",
#             postgresql.JSONB(),
#             nullable=False,
#             server_default=sa.text("'[]'::jsonb"),
#         ),
#         sa.Column(
#             "permissions",
#             postgresql.JSONB(),
#             nullable=False,
#             server_default=sa.text("'[]'::jsonb"),
#         ),

#         sa.Column("tenant_slug", sa.String(100), nullable=False),

#         sa.Column(
#             "is_active",
#             sa.Boolean(),
#             nullable=False,
#             server_default=sa.text("true"),
#         ),
#         sa.Column(
#             "is_verified",
#             sa.Boolean(),
#             nullable=False,
#             server_default=sa.text("false"),
#         ),
#         sa.Column(
#             "is_superuser",
#             sa.Boolean(),
#             nullable=False,
#             server_default=sa.text("false"),
#         ),

#         sa.Column(
#             "created_at",
#             sa.DateTime(timezone=True),
#             nullable=False,
#             server_default=sa.text("CURRENT_TIMESTAMP"),
#         ),
#         sa.Column(
#             "updated_at",
#             sa.DateTime(timezone=True),
#             nullable=False,
#             server_default=sa.text("CURRENT_TIMESTAMP"),
#         ),
#         sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
#         sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),

#         sa.Column(
#             "preferences",
#             postgresql.JSONB(),
#             nullable=False,
#             server_default=sa.text("'{}'::jsonb"),
#         ),

#         sa.PrimaryKeyConstraint("id"),
#         schema=schema,  # 🔥 THIS IS THE FIX
#     )

#     # -------------------------------
#     # INDEXES (SCHEMA AWARE)
#     # -------------------------------
#     op.create_index(
#         "ix_users_keycloak_id",
#         "users",
#         ["keycloak_id"],
#         unique=True,
#         schema=schema,
#     )

#     op.create_index(
#         "ix_users_email",
#         "users",
#         ["email"],
#         unique=True,
#         schema=schema,
#     )

#     op.create_index(
#         "ix_users_username",
#         "users",
#         ["username"],
#         schema=schema,
#     )

#     op.create_index(
#         "ix_users_tenant_slug",
#         "users",
#         ["tenant_slug"],
#         schema=schema,
#     )

#     op.create_index(
#         "ix_users_is_active",
#         "users",
#         ["is_active"],
#         schema=schema,
#     )

#     op.create_index(
#         "ix_users_created_at",
#         "users",
#         ["created_at"],
#         schema=schema,
#     )

#     op.create_index(
#         "ix_users_tenant_active",
#         "users",
#         ["tenant_slug", "is_active"],
#         schema=schema,
#     )


# def downgrade() -> None:
#     """
#     Drop tenant-specific tables.
#     """

#     schema = context.get_context().version_table_schema

#     op.drop_index("ix_users_tenant_active", table_name="users", schema=schema)
#     op.drop_index("ix_users_created_at", table_name="users", schema=schema)
#     op.drop_index("ix_users_is_active", table_name="users", schema=schema)
#     op.drop_index("ix_users_tenant_slug", table_name="users", schema=schema)
#     op.drop_index("ix_users_username", table_name="users", schema=schema)
#     op.drop_index("ix_users_email", table_name="users", schema=schema)
#     op.drop_index("ix_users_keycloak_id", table_name="users", schema=schema)

#     op.drop_table("users", schema=schema)


"""
Add tenant schema tables (users, agents, etc.)

Revision ID: a93ad6fadec3
Revises: c1d684656a7d
Create Date: 2025-12-17
"""

from typing import Sequence, Union
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a93ad6fadec3"
down_revision: Union[str, None] = "c1d684656a7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create tenant-specific tables inside the tenant schema.
    This migration should ONLY be run in tenant schemas, not public.
    """
    
    # Get the target schema from context
    schema = context.get_context().version_table_schema
    
    if not schema or schema == "public":
        print(f"[Migration] Skipping - this migration is only for tenant schemas")
        return
    
    print(f"[Migration] Creating tables in schema: {schema}")
    
    # Verify we're in the right schema
    conn = op.get_bind()
    result = conn.execute(sa.text("SHOW search_path"))
    current_path = result.scalar()
    print(f"[Migration] Current search_path: {current_path}")
    
    # -------------------------------
    # USERS TABLE
    # -------------------------------
    print(f"[Migration] Creating users table in {schema}")
    
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("keycloak_id", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column(
            "roles",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "permissions",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("tenant_slug", sa.String(100), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "preferences",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=schema,
    )
    
    # Create indexes
    op.create_index(
        "ix_users_keycloak_id",
        "users",
        ["keycloak_id"],
        unique=True,
        schema=schema,
    )
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
        schema=schema,
    )
    op.create_index(
        "ix_users_username",
        "users",
        ["username"],
        schema=schema,
    )
    op.create_index(
        "ix_users_tenant_slug",
        "users",
        ["tenant_slug"],
        schema=schema,
    )
    op.create_index(
        "ix_users_is_active",
        "users",
        ["is_active"],
        schema=schema,
    )
    op.create_index(
        "ix_users_created_at",
        "users",
        ["created_at"],
        schema=schema,
    )
    op.create_index(
        "ix_users_tenant_active",
        "users",
        ["tenant_slug", "is_active"],
        schema=schema,
    )
    
    print(f"[Migration] ✓ Users table created in {schema}")
    
    # -------------------------------
    # AGENTS TABLE
    # -------------------------------
    print(f"[Migration] Creating agents table in {schema}")
    
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("workflow", sa.String(255), nullable=False),
        sa.Column(
            "config",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            [f"{schema}.users.id"],
            ondelete="SET NULL",
        ),
        schema=schema,
    )
    
    op.create_index(
        "ix_agents_name",
        "agents",
        ["name"],
        unique=True,
        schema=schema,
    )
    op.create_index(
        "ix_agents_active",
        "agents",
        ["active"],
        schema=schema,
    )
    
    print(f"[Migration] ✓ Agents table created in {schema}")
    
    # -------------------------------
    # AGENT EXECUTION LOGS TABLE
    # -------------------------------
    print(f"[Migration] Creating agent_execution_logs table in {schema}")
    
    op.create_table(
        "agent_execution_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("execution_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("input_data", postgresql.JSONB(), nullable=True),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_by", sa.Integer(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            [f"{schema}.agents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["started_by"],
            [f"{schema}.users.id"],
            ondelete="SET NULL",
        ),
        schema=schema,
    )
    
    op.create_index(
        "ix_agent_execution_logs_agent_id",
        "agent_execution_logs",
        ["agent_id"],
        schema=schema,
    )
    op.create_index(
        "ix_agent_execution_logs_execution_id",
        "agent_execution_logs",
        ["execution_id"],
        unique=True,
        schema=schema,
    )
    op.create_index(
        "ix_agent_execution_logs_status",
        "agent_execution_logs",
        ["status"],
        schema=schema,
    )
    
    print(f"[Migration] ✓ Agent execution logs table created in {schema}")
    
    # -------------------------------
    # HITL RECORDS TABLE
    # -------------------------------
    print(f"[Migration] Creating hitl_records table in {schema}")
    
    op.create_table(
        "hitl_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(255), nullable=False),
        sa.Column("execution_id", sa.String(255), nullable=True),
        sa.Column(
            "input_data",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "priority",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'normal'"),
        ),
        sa.Column("feedback", postgresql.JSONB(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timeout_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "escalated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            [f"{schema}.agents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to"],
            [f"{schema}.users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            [f"{schema}.users.id"],
            ondelete="SET NULL",
        ),
        schema=schema,
    )
    
    op.create_index(
        "ix_hitl_records_agent_id",
        "hitl_records",
        ["agent_id"],
        schema=schema,
    )
    op.create_index(
        "ix_hitl_records_agent_name",
        "hitl_records",
        ["agent_name"],
        schema=schema,
    )
    op.create_index(
        "ix_hitl_records_execution_id",
        "hitl_records",
        ["execution_id"],
        schema=schema,
    )
    op.create_index(
        "ix_hitl_records_status",
        "hitl_records",
        ["status"],
        schema=schema,
    )
    op.create_index(
        "ix_hitl_records_priority",
        "hitl_records",
        ["priority"],
        schema=schema,
    )
    op.create_index(
        "ix_hitl_records_escalated",
        "hitl_records",
        ["escalated"],
        schema=schema,
    )
    
    print(f"[Migration] ✓ HITL records table created in {schema}")
    print(f"[Migration] ✅ All tables created successfully in {schema}")


def downgrade() -> None:
    """
    Drop tenant-specific tables.
    """
    schema = context.get_context().version_table_schema
    
    if not schema or schema == "public":
        print(f"[Migration] Skipping downgrade - this migration is only for tenant schemas")
        return
    
    print(f"[Migration] Dropping tables from schema: {schema}")
    
    # Drop in reverse order (due to foreign keys)
    op.drop_table("hitl_records", schema=schema)
    op.drop_table("agent_execution_logs", schema=schema)
    op.drop_table("agents", schema=schema)
    op.drop_table("users", schema=schema)
    
    print(f"[Migration] ✓ All tables dropped from {schema}")
