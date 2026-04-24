"""
001_all_tables.py — Single consolidated migration
==================================================
Creates ALL tables in whatever schema Alembic points it at.
This runs identically for:
  - public schema          (alembic upgrade head)
  - any tenant schema      (auto-run when a new tenant is created)

No schema guards. No branching. One head. Works like django-tenants.

Revision ID: 001_all_tables
Revises:
"""

from typing import Sequence, Union
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

revision: str = "001_all_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s() -> str:
    """Return the current target schema (public or a tenant schema)."""
    return context.get_context().version_table_schema or "public"


def _exists(conn, schema: str, table: str) -> bool:
    result = conn.execute(
        text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :s AND table_name = :t
        """),
        {"s": schema, "t": table},
    )
    return result.fetchone() is not None


def _create_enum(conn, schema: str, name: str, values: list) -> None:
    vals = ", ".join(f"'{v}'" for v in values)
    conn.execute(sa.DDL(f"""
        DO $$ BEGIN
            CREATE TYPE "{schema}".{name} AS ENUM ({vals});
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    schema = _s()
    conn = op.get_bind()
    print(f"[001_all_tables] Running upgrade for schema: {schema}")

    # =========================================================================
    # 1. TENANTS  — registry of all tenant schemas
    # =========================================================================
    if not _exists(conn, schema, "tenants"):
        op.create_table(
            "tenants",
            sa.Column("slug",         sa.String(100), nullable=False),
            sa.Column("schema_name",  sa.String(100), nullable=False),
            sa.Column("name",         sa.String(255), nullable=False),
            sa.Column("description",  sa.Text(),      nullable=True),
            sa.Column("status",       sa.String(20),  nullable=False, server_default="active"),
            sa.Column("config",       sa.JSON(),      nullable=True),
            sa.Column("max_users",    sa.Integer(),   nullable=True),
            sa.Column("admin_email",  sa.String(255), nullable=True),
            sa.Column("created_at",   sa.DateTime(),  nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at",   sa.DateTime(),  nullable=False, server_default=sa.text("now()")),
            sa.Column("suspended_at", sa.DateTime(),  nullable=True),
            sa.PrimaryKeyConstraint("slug"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_tenants_schema", "tenants", ["schema_name"], unique=True,  schema=schema)
        op.create_index(f"ix_{schema}_tenants_slug",   "tenants", ["slug"],        unique=False, schema=schema)
        print(f"[001_all_tables] ✓ tenants")

    # =========================================================================
    # 2. USERS
    # =========================================================================
    if not _exists(conn, schema, "users"):
        op.create_table(
            "users",
            sa.Column("id",                    sa.Integer(),    nullable=False),
            sa.Column("keycloak_id",            sa.String(255),  nullable=True),
            sa.Column("email",                  sa.String(255),  nullable=False),
            sa.Column("username",               sa.String(255),  nullable=True),
            sa.Column("hashed_password",        sa.String(255),  nullable=True),
            sa.Column("full_name",              sa.String(255),  nullable=True),
            sa.Column("avatar_url",             sa.String(500),  nullable=True),
            sa.Column("phone",                  sa.String(50),   nullable=True),
            sa.Column("roles",                  postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("permissions",            postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("tenant_slug",            sa.String(100),  nullable=True),
            sa.Column("is_active",              sa.Boolean(),    nullable=False, server_default=sa.text("true")),
            sa.Column("is_verified",            sa.Boolean(),    nullable=False, server_default=sa.text("false")),
            sa.Column("is_superuser",           sa.Boolean(),    nullable=False, server_default=sa.text("false")),
            sa.Column("created_at",             sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at",             sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("last_login",             sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_seen",              sa.DateTime(timezone=True), nullable=True),
            sa.Column("preferences",            postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            # Invitation fields
            sa.Column("invitation_status",      sa.String(20),  nullable=True, server_default="accepted"),
            sa.Column("invitation_token",       sa.String(255), nullable=True),
            sa.Column("invited_by",             sa.Integer(),   nullable=True),
            sa.Column("invited_at",             sa.DateTime(timezone=True), nullable=True),
            sa.Column("accepted_at",            sa.DateTime(timezone=True), nullable=True),
            sa.Column("invitation_expires_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("provisioning_method",    sa.String(50),  nullable=True, server_default="manual"),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_users_email",    "users", ["email"],       unique=True,  schema=schema)
        op.create_index(f"ix_{schema}_users_keycloak", "users", ["keycloak_id"], unique=False, schema=schema)
        op.create_index(f"ix_{schema}_users_active",   "users", ["is_active"],               schema=schema)
        op.create_index(f"ix_{schema}_users_tenant",   "users", ["tenant_slug"],              schema=schema)
        # Self-referential FK for invited_by
        conn.execute(sa.DDL(f"""
            ALTER TABLE "{schema}".users
                ADD CONSTRAINT fk_{schema}_users_invited_by
                FOREIGN KEY (invited_by) REFERENCES "{schema}".users(id)
                ON DELETE SET NULL;
        """))
        print(f"[001_all_tables] ✓ users")

    # =========================================================================
    # 3. AGENTS
    # =========================================================================
    if not _exists(conn, schema, "agents"):
        op.create_table(
            "agents",
            sa.Column("id",          sa.Integer(),    nullable=False),
            sa.Column("name",        sa.String(255),  nullable=False),
            sa.Column("description", sa.Text(),       nullable=True),
            sa.Column("workflow",    sa.String(255),  nullable=False),
            sa.Column("config",      postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("active",      sa.Boolean(),    nullable=False, server_default=sa.text("true")),
            sa.Column("version",     sa.Integer(),    nullable=False, server_default=sa.text("1")),
            sa.Column("created_by",  sa.Integer(),    nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at",  sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["created_by"], [f'{schema}.users.id'], ondelete="SET NULL"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_agents_name",   "agents", ["name"],   unique=True,  schema=schema)
        op.create_index(f"ix_{schema}_agents_active", "agents", ["active"],               schema=schema)
        print(f"[001_all_tables] ✓ agents")

    # =========================================================================
    # 4. AGENT EXECUTION LOGS
    # =========================================================================
    if not _exists(conn, schema, "agent_execution_logs"):
        op.create_table(
            "agent_execution_logs",
            sa.Column("id",           sa.Integer(),    nullable=False),
            sa.Column("agent_id",     sa.Integer(),    nullable=False),
            sa.Column("execution_id", sa.String(255),  nullable=False),
            sa.Column("status",       sa.String(50),   nullable=False),
            sa.Column("input_data",   postgresql.JSONB(), nullable=True),
            sa.Column("output_data",  postgresql.JSONB(), nullable=True),
            sa.Column("error",        sa.Text(),       nullable=True),
            sa.Column("duration_ms",  sa.Integer(),    nullable=True),
            sa.Column("started_by",   sa.Integer(),    nullable=True),
            sa.Column("started_at",   sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["agent_id"],   [f'{schema}.agents.id'], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["started_by"], [f'{schema}.users.id'],  ondelete="SET NULL"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_ael_agent",    "agent_execution_logs", ["agent_id"],     schema=schema)
        op.create_index(f"ix_{schema}_ael_exec_id",  "agent_execution_logs", ["execution_id"], unique=True, schema=schema)
        op.create_index(f"ix_{schema}_ael_status",   "agent_execution_logs", ["status"],       schema=schema)
        print(f"[001_all_tables] ✓ agent_execution_logs")

    # =========================================================================
    # 5. HITL RECORDS
    # =========================================================================
    if not _exists(conn, schema, "hitl_records"):
        op.create_table(
            "hitl_records",
            sa.Column("id",           sa.Integer(),    nullable=False),
            sa.Column("agent_id",     sa.Integer(),    nullable=False),
            sa.Column("agent_name",   sa.String(255),  nullable=False),
            sa.Column("execution_id", sa.String(255),  nullable=True),
            sa.Column("input_data",   postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("output_data",  postgresql.JSONB(), nullable=True),
            sa.Column("status",       sa.String(50),   nullable=False, server_default=sa.text("'pending'")),
            sa.Column("priority",     sa.String(20),   nullable=False, server_default=sa.text("'normal'")),
            sa.Column("feedback",     postgresql.JSONB(), nullable=True),
            sa.Column("assigned_to",  sa.Integer(),    nullable=True),
            sa.Column("reviewed_by",  sa.Integer(),    nullable=True),
            sa.Column("reviewed_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("timeout_at",   sa.DateTime(timezone=True), nullable=True),
            sa.Column("escalated",    sa.Boolean(),    nullable=False, server_default=sa.text("false")),
            sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at",   sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at",   sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["agent_id"],    [f'{schema}.agents.id'], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["assigned_to"], [f'{schema}.users.id'],  ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["reviewed_by"], [f'{schema}.users.id'],  ondelete="SET NULL"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_hitl_agent",    "hitl_records", ["agent_id"], schema=schema)
        op.create_index(f"ix_{schema}_hitl_status",   "hitl_records", ["status"],   schema=schema)
        op.create_index(f"ix_{schema}_hitl_priority", "hitl_records", ["priority"], schema=schema)
        print(f"[001_all_tables] ✓ hitl_records")

    # =========================================================================
    # 6. AGENT BUILDER CONFIGS
    # =========================================================================
    if not _exists(conn, schema, "agent_builder_configs"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".agent_builder_configs (
                id                         SERIAL PRIMARY KEY,
                agent_id                   INTEGER NOT NULL REFERENCES "{schema}".agents(id) ON DELETE CASCADE,
                llm_provider               VARCHAR(50)   NOT NULL DEFAULT 'openai',
                llm_model                  VARCHAR(100)  NOT NULL DEFAULT 'gpt-4',
                llm_temperature            DECIMAL(3,2)  DEFAULT 0.7,
                llm_max_tokens             INTEGER       DEFAULT 2000,
                llm_api_endpoint           TEXT,
                llm_api_key_ref            VARCHAR(255),
                input_schema               JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                input_preprocessing        JSONB DEFAULT '[]'::jsonb,
                input_validation_rules     JSONB DEFAULT '{{}}'::jsonb,
                enabled_tools              JSONB NOT NULL DEFAULT '[]'::jsonb,
                tool_timeout_seconds       INTEGER DEFAULT 300,
                max_tool_calls             INTEGER DEFAULT 10,
                db_connection_id           INTEGER,
                db_queries                 JSONB DEFAULT '[]'::jsonb,
                db_write_enabled           BOOLEAN DEFAULT FALSE,
                api_endpoints              JSONB DEFAULT '[]'::jsonb,
                api_auth_method            VARCHAR(50),
                api_rate_limit             INTEGER,
                data_sources               JSONB DEFAULT '[]'::jsonb,
                data_refresh_interval      INTEGER,
                output_format              VARCHAR(50) NOT NULL DEFAULT 'json',
                output_destination         JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                output_schema              JSONB DEFAULT '{{}}'::jsonb,
                output_transformation      JSONB DEFAULT '{{}}'::jsonb,
                trigger_type               VARCHAR(50) NOT NULL DEFAULT 'manual',
                trigger_config             JSONB DEFAULT '{{}}'::jsonb,
                schedule_cron              VARCHAR(100),
                event_listeners            JSONB DEFAULT '[]'::jsonb,
                hitl_enabled               BOOLEAN NOT NULL DEFAULT FALSE,
                hitl_trigger_conditions    JSONB DEFAULT '{{}}'::jsonb,
                hitl_approval_required     BOOLEAN DEFAULT FALSE,
                hitl_timeout_minutes       INTEGER DEFAULT 60,
                hitl_escalation_rules      JSONB DEFAULT '{{}}'::jsonb,
                max_execution_time_seconds INTEGER DEFAULT 3600,
                retry_policy               JSONB DEFAULT '{{"max_retries":3,"backoff_multiplier":2}}'::jsonb,
                error_handling_strategy    VARCHAR(50) DEFAULT 'fail',
                conditional_branches       JSONB DEFAULT '[]'::jsonb,
                loop_configuration         JSONB DEFAULT '{{}}'::jsonb,
                parallel_execution_enabled BOOLEAN DEFAULT FALSE,
                logging_level              VARCHAR(20) DEFAULT 'INFO',
                metrics_enabled            BOOLEAN DEFAULT TRUE,
                alert_rules                JSONB DEFAULT '[]'::jsonb,
                version                    INTEGER NOT NULL DEFAULT 1,
                change_log                 TEXT,
                created_at                 TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at                 TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(agent_id, version)
            );
            CREATE INDEX ix_{schema}_abc_agent ON "{schema}".agent_builder_configs(agent_id);
        """))
        print(f"[001_all_tables] ✓ agent_builder_configs")

    # =========================================================================
    # 7. AGENT EXECUTION TRIGGERS
    # =========================================================================
    if not _exists(conn, schema, "agent_execution_triggers"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".agent_execution_triggers (
                id              SERIAL PRIMARY KEY,
                agent_id        INTEGER NOT NULL REFERENCES "{schema}".agents(id) ON DELETE CASCADE,
                trigger_name    VARCHAR(255) NOT NULL,
                trigger_type    VARCHAR(50) NOT NULL CHECK (
                    trigger_type IN ('scheduled','webhook','event','manual','file_upload','database_change','api_call')
                ),
                conditions      JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                filters         JSONB DEFAULT '{{}}'::jsonb,
                webhook_url     TEXT,
                webhook_secret  VARCHAR(255),
                webhook_method  VARCHAR(10) DEFAULT 'POST',
                cron_expression VARCHAR(100),
                timezone        VARCHAR(50) DEFAULT 'UTC',
                is_enabled      BOOLEAN NOT NULL DEFAULT TRUE,
                last_triggered  TIMESTAMP WITH TIME ZONE,
                trigger_count   INTEGER DEFAULT 0,
                created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX ix_{schema}_aet_agent ON "{schema}".agent_execution_triggers(agent_id);
        """))
        print(f"[001_all_tables] ✓ agent_execution_triggers")

    # =========================================================================
    # 8. AGENT VARIABLES
    # =========================================================================
    if not _exists(conn, schema, "agent_variables"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".agent_variables (
                id              SERIAL PRIMARY KEY,
                agent_id        INTEGER REFERENCES "{schema}".agents(id) ON DELETE CASCADE,
                variable_name   VARCHAR(255) NOT NULL,
                variable_type   VARCHAR(50) NOT NULL CHECK (
                    variable_type IN ('string','number','boolean','secret','json','array')
                ),
                variable_value  TEXT,
                encrypted_value TEXT,
                description     TEXT,
                is_secret       BOOLEAN NOT NULL DEFAULT FALSE,
                is_required     BOOLEAN NOT NULL DEFAULT FALSE,
                default_value   TEXT,
                scope           VARCHAR(50) NOT NULL DEFAULT 'agent',
                created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(agent_id, variable_name)
            );
            CREATE INDEX ix_{schema}_av_agent ON "{schema}".agent_variables(agent_id);
        """))
        print(f"[001_all_tables] ✓ agent_variables")

    # =========================================================================
    # 9. AGENT VERSIONS
    # =========================================================================
    if not _exists(conn, schema, "agent_versions"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".agent_versions (
                id                      SERIAL PRIMARY KEY,
                agent_id                INTEGER NOT NULL REFERENCES "{schema}".agents(id) ON DELETE CASCADE,
                version_number          INTEGER NOT NULL,
                version_tag             VARCHAR(50),
                config_snapshot         JSONB NOT NULL,
                builder_config_snapshot JSONB,
                change_description      TEXT,
                changed_by              INTEGER,
                is_deployed             BOOLEAN NOT NULL DEFAULT FALSE,
                deployed_at             TIMESTAMP WITH TIME ZONE,
                created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(agent_id, version_number)
            );
            CREATE INDEX ix_{schema}_aver_agent ON "{schema}".agent_versions(agent_id);
        """))
        print(f"[001_all_tables] ✓ agent_versions")

    # =========================================================================
    # 10. AUDIT LOGS
    # =========================================================================
    if not _exists(conn, schema, "audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id",            sa.Integer(),    nullable=False),
            sa.Column("timestamp",     sa.DateTime(),   nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("user_id",       sa.Integer(),    nullable=True),
            sa.Column("user_email",    sa.String(255),  nullable=True),
            sa.Column("ip_address",    sa.String(45),   nullable=True),
            sa.Column("user_agent",    sa.Text(),       nullable=True),
            sa.Column("action",        sa.String(100),  nullable=False),
            sa.Column("resource_type", sa.String(50),   nullable=True),
            sa.Column("resource_id",   sa.String(255),  nullable=True),
            sa.Column("details",       postgresql.JSONB(), nullable=True),
            sa.Column("tenant_id",     sa.Integer(),    nullable=True),
            sa.Column("status",        sa.String(20),   nullable=False, server_default="success"),
            sa.Column("error_message", sa.Text(),       nullable=True),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_al_timestamp", "audit_logs", ["timestamp"],              schema=schema)
        op.create_index(f"ix_{schema}_al_user",      "audit_logs", ["user_id"],                schema=schema)
        op.create_index(f"ix_{schema}_al_action",    "audit_logs", ["action"],                 schema=schema)
        op.create_index(f"ix_{schema}_al_resource",  "audit_logs", ["resource_type","resource_id"], schema=schema)
        print(f"[001_all_tables] ✓ audit_logs")

    # =========================================================================
    # 11. NOTIFICATIONS
    # =========================================================================
    if not _exists(conn, schema, "notifications"):
        op.create_table(
            "notifications",
            sa.Column("id",                 sa.Integer(),    nullable=False),
            sa.Column("user_id",            sa.Integer(),    nullable=False),
            sa.Column("notification_type",  sa.String(50),   nullable=False),
            sa.Column("title",              sa.String(255),  nullable=False),
            sa.Column("message",            sa.Text(),       nullable=False),
            sa.Column("data",               postgresql.JSONB(), nullable=True),
            sa.Column("priority",           sa.String(20),   nullable=False, server_default="normal"),
            sa.Column("read",               sa.Boolean(),    nullable=False, server_default="false"),
            sa.Column("read_at",            sa.DateTime(),   nullable=True),
            sa.Column("channels",           postgresql.JSONB(), nullable=True),
            sa.Column("delivered_channels", postgresql.JSONB(), nullable=True),
            sa.Column("created_at",         sa.DateTime(),   nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("expires_at",         sa.DateTime(),   nullable=True),
            sa.Column("resource_type",      sa.String(50),   nullable=True),
            sa.Column("resource_id",        sa.String(255),  nullable=True),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_notif_user",    "notifications", ["user_id"],         schema=schema)
        op.create_index(f"ix_{schema}_notif_unread",  "notifications", ["user_id","read"],  schema=schema)
        op.create_index(f"ix_{schema}_notif_created", "notifications", ["created_at"],      schema=schema)
        print(f"[001_all_tables] ✓ notifications")

    # =========================================================================
    # 12. WORKFLOW TEMPLATES
    # =========================================================================
    if not _exists(conn, schema, "workflow_templates"):
        op.create_table(
            "workflow_templates",
            sa.Column("id",                  sa.Integer(),    nullable=False),
            sa.Column("name",                sa.String(255),  nullable=False),
            sa.Column("description",         sa.Text(),       nullable=True),
            sa.Column("category",            sa.String(100),  nullable=False),
            sa.Column("tags",                postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("workflow_definition", postgresql.JSONB(), nullable=False),
            sa.Column("config_schema",       postgresql.JSONB(), nullable=False, server_default="{}"),
            sa.Column("author_id",           sa.Integer(),    nullable=True),
            sa.Column("author_tenant",       sa.String(100),  nullable=True),
            sa.Column("is_official",         sa.Boolean(),    nullable=False, server_default="false"),
            sa.Column("is_public",           sa.Boolean(),    nullable=False, server_default="true"),
            sa.Column("install_count",       sa.Integer(),    nullable=False, server_default="0"),
            sa.Column("rating",              sa.Float(),      nullable=False, server_default="0.0"),
            sa.Column("review_count",        sa.Integer(),    nullable=False, server_default="0"),
            sa.Column("version",             sa.String(50),   nullable=False, server_default="1.0.0"),
            sa.Column("changelog",           sa.Text(),       nullable=True),
            sa.Column("is_premium",          sa.Boolean(),    nullable=False, server_default="false"),
            sa.Column("price",               sa.Float(),      nullable=False, server_default="0.0"),
            sa.Column("created_at",          sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at",          sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_wft_name",     "workflow_templates", ["name"],     schema=schema)
        op.create_index(f"ix_{schema}_wft_category", "workflow_templates", ["category"], schema=schema)
        print(f"[001_all_tables] ✓ workflow_templates")

    # =========================================================================
    # 13. SSO CONFIGURATIONS
    # =========================================================================
    if not _exists(conn, schema, "sso_configurations"):
        op.create_table(
            "sso_configurations",
            sa.Column("id",                    sa.Integer(),    nullable=False),
            sa.Column("tenant_slug",            sa.String(100),  nullable=False),
            sa.Column("provider_type",          sa.String(50),   nullable=False),
            sa.Column("provider_name",          sa.String(255),  nullable=False),
            sa.Column("client_id",              sa.String(500),  nullable=True),
            sa.Column("client_secret",          sa.Text(),       nullable=True),
            sa.Column("authorization_endpoint", sa.String(500),  nullable=True),
            sa.Column("token_endpoint",         sa.String(500),  nullable=True),
            sa.Column("userinfo_endpoint",      sa.String(500),  nullable=True),
            sa.Column("jwks_uri",               sa.String(500),  nullable=True),
            sa.Column("saml_entity_id",         sa.String(500),  nullable=True),
            sa.Column("saml_sso_url",           sa.String(500),  nullable=True),
            sa.Column("saml_certificate",       sa.Text(),       nullable=True),
            sa.Column("scopes",                 postgresql.JSONB(), nullable=False, server_default='["openid","email","profile"]'),
            sa.Column("redirect_uri",           sa.String(500),  nullable=False),
            sa.Column("attribute_mapping",      postgresql.JSONB(), nullable=False, server_default='{"email":"email","name":"full_name"}'),
            sa.Column("is_enabled",             sa.Boolean(),    nullable=False, server_default="true"),
            sa.Column("auto_provision_users",   sa.Boolean(),    nullable=False, server_default="true"),
            sa.Column("created_at",             sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at",             sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_sso_tenant",          "sso_configurations", ["tenant_slug"],                  schema=schema)
        op.create_index(f"ix_{schema}_sso_tenant_provider", "sso_configurations", ["tenant_slug","provider_type"],
                        unique=True, schema=schema)
        print(f"[001_all_tables] ✓ sso_configurations")

    # =========================================================================
    # 14. AI MODELS
    # =========================================================================
    if not _exists(conn, schema, "ai_models"):
        op.create_table(
            "ai_models",
            sa.Column("id",                        sa.Integer(),    nullable=False),
            sa.Column("name",                      sa.String(255),  nullable=False),
            sa.Column("model_id",                  sa.String(255),  nullable=False),
            sa.Column("provider",                  sa.String(50),   nullable=False),
            sa.Column("version",                   sa.String(50),   nullable=True),
            sa.Column("description",               sa.Text(),       nullable=True),
            sa.Column("capabilities",              postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("context_window",            sa.Integer(),    nullable=True),
            sa.Column("max_tokens",                sa.Integer(),    nullable=True),
            sa.Column("input_cost_per_1m",         sa.Float(),      nullable=True),
            sa.Column("output_cost_per_1m",        sa.Float(),      nullable=True),
            sa.Column("status",                    sa.String(50),   nullable=False, server_default="active"),
            sa.Column("is_default",                sa.Boolean(),    nullable=False, server_default="false"),
            sa.Column("is_enabled",                sa.Boolean(),    nullable=False, server_default="true"),
            sa.Column("default_parameters",        postgresql.JSONB(), nullable=False, server_default='{"temperature":0.7,"max_tokens":1000}'),
            sa.Column("tags",                      postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("created_at",                sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at",                sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("model_id", name=f"uq_{schema}_ai_models_model_id"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_aim_provider", "ai_models", ["provider"],   schema=schema)
        op.create_index(f"ix_{schema}_aim_enabled",  "ai_models", ["is_enabled"], schema=schema)
        print(f"[001_all_tables] ✓ ai_models")

    # =========================================================================
    # 15. MODEL PRICING
    # =========================================================================
    if not _exists(conn, schema, "model_pricing"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".model_pricing (
                id                 SERIAL PRIMARY KEY,
                model_provider     VARCHAR(50)   NOT NULL,
                model_name         VARCHAR(100)  NOT NULL,
                model_version      VARCHAR(50),
                input_cost_per_1k  NUMERIC(12,8) NOT NULL,
                output_cost_per_1k NUMERIC(12,8) NOT NULL,
                cache_read_per_1k  NUMERIC(12,8) DEFAULT 0,
                cache_write_per_1k NUMERIC(12,8) DEFAULT 0,
                effective_from     TIMESTAMP     NOT NULL DEFAULT NOW(),
                effective_until    TIMESTAMP,
                currency           VARCHAR(3)    DEFAULT 'USD',
                active             BOOLEAN       DEFAULT TRUE,
                notes              VARCHAR(500),
                source_url         VARCHAR(500),
                created_at         TIMESTAMP     DEFAULT NOW(),
                updated_at         TIMESTAMP     DEFAULT NOW()
            );
            CREATE INDEX ix_{schema}_mp_provider ON "{schema}".model_pricing(model_provider, model_name);
            CREATE INDEX ix_{schema}_mp_active    ON "{schema}".model_pricing(active);
        """))
        print(f"[001_all_tables] ✓ model_pricing")

    # =========================================================================
    # 16. AGENT TEMPLATES
    # =========================================================================
    if not _exists(conn, schema, "agent_templates"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".agent_templates (
                id                 SERIAL PRIMARY KEY,
                name               VARCHAR(255) NOT NULL UNIQUE,
                description        TEXT,
                category           VARCHAR(100) NOT NULL,
                icon               VARCHAR(50),
                template_config    JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                default_tools      JSONB NOT NULL DEFAULT '[]'::jsonb,
                required_fields    JSONB NOT NULL DEFAULT '[]'::jsonb,
                workflow_type      VARCHAR(100) NOT NULL,
                node_configuration JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                is_official        BOOLEAN NOT NULL DEFAULT FALSE,
                is_public          BOOLEAN NOT NULL DEFAULT TRUE,
                created_by         INTEGER REFERENCES "{schema}".users(id) ON DELETE SET NULL,
                created_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX ix_{schema}_at_category ON "{schema}".agent_templates(category);
            CREATE INDEX ix_{schema}_at_workflow  ON "{schema}".agent_templates(workflow_type);
        """))
        print(f"[001_all_tables] ✓ agent_templates")

    # =========================================================================
    # 17. DATABASE CONNECTIONS
    # =========================================================================
    if not _exists(conn, schema, "database_connections"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".database_connections (
                id                         SERIAL PRIMARY KEY,
                name                       VARCHAR(255) NOT NULL,
                description                TEXT,
                db_type                    VARCHAR(50)  NOT NULL,
                host                       VARCHAR(255),
                port                       INTEGER,
                database_name              VARCHAR(255),
                username                   VARCHAR(255),
                password_encrypted         TEXT,
                connection_string_template TEXT,
                pool_size                  INTEGER DEFAULT 5,
                max_overflow               INTEGER DEFAULT 10,
                pool_timeout               INTEGER DEFAULT 30,
                ssl_enabled                BOOLEAN DEFAULT TRUE,
                ssl_cert                   TEXT,
                created_by                 INTEGER REFERENCES "{schema}".users(id) ON DELETE SET NULL,
                allowed_operations         JSONB DEFAULT '["read"]'::jsonb,
                is_active                  BOOLEAN NOT NULL DEFAULT TRUE,
                last_tested                TIMESTAMP WITH TIME ZONE,
                last_test_status           VARCHAR(50),
                created_at                 TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at                 TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """))
        print(f"[001_all_tables] ✓ database_connections")

    # =========================================================================
    # 18. API CONFIGURATIONS
    # =========================================================================
    if not _exists(conn, schema, "api_configurations"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".api_configurations (
                id                    SERIAL PRIMARY KEY,
                name                  VARCHAR(255) NOT NULL,
                description           TEXT,
                base_url              TEXT NOT NULL,
                api_version           VARCHAR(50),
                auth_type             VARCHAR(50)  NOT NULL,
                auth_credentials      JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                oauth_config          JSONB,
                rate_limit_per_minute INTEGER,
                rate_limit_per_hour   INTEGER,
                default_headers       JSONB DEFAULT '{{}}'::jsonb,
                timeout_seconds       INTEGER DEFAULT 30,
                retry_config          JSONB DEFAULT '{{"max_retries":3,"backoff":"exponential"}}'::jsonb,
                documentation_url     TEXT,
                example_requests      JSONB DEFAULT '[]'::jsonb,
                created_by            INTEGER REFERENCES "{schema}".users(id) ON DELETE SET NULL,
                is_active             BOOLEAN NOT NULL DEFAULT TRUE,
                created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """))
        print(f"[001_all_tables] ✓ api_configurations")

    # =========================================================================
    # 19. TOOL REGISTRY
    # =========================================================================
    if not _exists(conn, schema, "tool_registry"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".tool_registry (
                id                    SERIAL PRIMARY KEY,
                name                  VARCHAR(255) NOT NULL UNIQUE,
                display_name          VARCHAR(255) NOT NULL,
                description           TEXT NOT NULL,
                tool_type             VARCHAR(50)  NOT NULL,
                category              VARCHAR(100) NOT NULL,
                implementation_type   VARCHAR(50)  NOT NULL,
                code_reference        TEXT,
                input_schema          JSONB NOT NULL,
                output_schema         JSONB NOT NULL,
                parameter_hints       JSONB DEFAULT '{{}}'::jsonb,
                requires_auth         BOOLEAN DEFAULT FALSE,
                required_permissions  JSONB DEFAULT '[]'::jsonb,
                cost_per_call         DECIMAL(10,4) DEFAULT 0,
                avg_execution_time_ms INTEGER,
                timeout_seconds       INTEGER DEFAULT 30,
                is_active             BOOLEAN NOT NULL DEFAULT TRUE,
                is_premium            BOOLEAN NOT NULL DEFAULT FALSE,
                version               VARCHAR(50) NOT NULL DEFAULT '1.0.0',
                author                VARCHAR(255),
                documentation_url     TEXT,
                example_usage         JSONB DEFAULT '{{}}'::jsonb,
                created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """))
        print(f"[001_all_tables] ✓ tool_registry")

    # =========================================================================
    # 20. COMPUTATIONAL AUDIT USAGE
    # =========================================================================
    if not _exists(conn, schema, "computational_audit_usage"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".computational_audit_usage (
                id                  SERIAL PRIMARY KEY,
                execution_id        VARCHAR(255) NOT NULL,
                agent_id            INTEGER      NOT NULL,
                stage_name          VARCHAR(100) NOT NULL,
                step_number         INTEGER,
                node_name           VARCHAR(100),
                model_provider      VARCHAR(50),
                model_name          VARCHAR(100),
                model_version       VARCHAR(50),
                input_tokens        INTEGER DEFAULT 0,
                output_tokens       INTEGER DEFAULT 0,
                cache_read_tokens   INTEGER DEFAULT 0,
                cache_write_tokens  INTEGER DEFAULT 0,
                total_tokens        INTEGER DEFAULT 0,
                unit_cost_input     NUMERIC(12,8) DEFAULT 0,
                unit_cost_output    NUMERIC(12,8) DEFAULT 0,
                computed_cost_usd   NUMERIC(16,8) DEFAULT 0,
                latency_ms          INTEGER,
                ttft_ms             INTEGER,
                retry_count         INTEGER DEFAULT 0,
                tool_calls_count    INTEGER DEFAULT 0,
                tool_calls_data     JSONB,
                prompt_hash         VARCHAR(64),
                finish_reason       VARCHAR(50),
                model_metadata      JSONB,
                created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_{schema}_cau_agent
                    FOREIGN KEY (agent_id) REFERENCES "{schema}".agents(id) ON DELETE CASCADE,
                CONSTRAINT fk_{schema}_cau_exec
                    FOREIGN KEY (execution_id) REFERENCES "{schema}".agent_execution_logs(execution_id) ON DELETE CASCADE
            );
            CREATE INDEX ix_{schema}_cau_exec    ON "{schema}".computational_audit_usage(execution_id);
            CREATE INDEX ix_{schema}_cau_agent   ON "{schema}".computational_audit_usage(agent_id);
            CREATE INDEX ix_{schema}_cau_created ON "{schema}".computational_audit_usage(created_at);
        """))
        print(f"[001_all_tables] ✓ computational_audit_usage")

    # =========================================================================
    # 21–29. WORKERS COMPENSATION AUDIT TABLES
    # =========================================================================

    # ENUM types (idempotent)
    _create_enum(conn, schema, "audit_status_enum",
        ["pending","ingesting","processing","review","approved","completed","rejected"])
    _create_enum(conn, schema, "variance_root_cause",
        ["officer_mismatch","class_code_mismatch","frequency_gap","payroll_variance","rate_discrepancy","none"])
    _create_enum(conn, schema, "recommendation_enum",
        ["refund","additional_premium","clarification","no_action"])
    _create_enum(conn, schema, "data_source_enum",
        ["insured","payroll_provider","policy_config"])

    if not _exists(conn, schema, "wc_policies"):
        op.create_table(
            "wc_policies",
            sa.Column("id",                sa.Integer(),      nullable=False),
            sa.Column("policy_number",     sa.String(50),     nullable=False),
            sa.Column("insured_name",      sa.String(255),    nullable=False),
            sa.Column("effective_date",    sa.Date(),         nullable=False),
            sa.Column("expiration_date",   sa.Date(),         nullable=False),
            sa.Column("estimated_premium", sa.Numeric(15,2),  server_default="0.0"),
            sa.Column("payroll_frequency", sa.String(10),     server_default="1W"),
            sa.Column("state_code",        sa.String(5),      nullable=False),
            sa.Column("carrier_name",      sa.String(255)),
            sa.Column("broker_name",       sa.String(255)),
            sa.Column("is_active",         sa.Boolean(),      server_default=sa.text("true")),
            sa.Column("created_at",        sa.DateTime(),     server_default=sa.text("now()")),
            sa.Column("updated_at",        sa.DateTime(),     server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("policy_number", name=f"uq_{schema}_wcp_pn"),
            schema=schema,
        )
        op.create_index(f"ix_{schema}_wcp_pn", "wc_policies", ["policy_number"], schema=schema)
        print(f"[001_all_tables] ✓ wc_policies")

    if not _exists(conn, schema, "wc_policy_class_codes"):
        op.create_table(
            "wc_policy_class_codes",
            sa.Column("id",                  sa.Integer(),      nullable=False),
            sa.Column("policy_id",           sa.Integer(),      nullable=False),
            sa.Column("class_code",          sa.String(10),     nullable=False),
            sa.Column("class_desc",          sa.String(255)),
            sa.Column("state_code",          sa.String(5),      nullable=False),
            sa.Column("composite_rate",      sa.Numeric(10,6),  server_default="0.0"),
            sa.Column("exposure",            sa.Numeric(15,2),  server_default="0.0"),
            sa.Column("est_premium",         sa.Numeric(15,2),  server_default="0.0"),
            sa.Column("est_cc_premium",      sa.Numeric(15,2),  server_default="0.0"),
            sa.Column("endorsement_version", sa.String(10),     server_default="V1"),
            sa.Column("created_at",          sa.DateTime(),     server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["policy_id"], [f'{schema}.wc_policies.id'],
                                    name=f"fk_{schema}_wcpcc_policy", ondelete="CASCADE"),
            schema=schema,
        )
        print(f"[001_all_tables] ✓ wc_policy_class_codes")

    if not _exists(conn, schema, "wc_policy_officers"):
        op.create_table(
            "wc_policy_officers",
            sa.Column("id",            sa.Integer(),    nullable=False),
            sa.Column("policy_id",     sa.Integer(),    nullable=False),
            sa.Column("officer_name",  sa.String(255),  nullable=False),
            sa.Column("title",         sa.String(100)),
            sa.Column("is_on_payroll", sa.Boolean(),    server_default=sa.text("true")),
            sa.Column("ownership_pct", sa.Numeric(5,2), server_default="0.0"),
            sa.Column("state_code",    sa.String(5)),
            sa.Column("created_at",    sa.DateTime(),   server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["policy_id"], [f'{schema}.wc_policies.id'],
                                    name=f"fk_{schema}_wcpo_policy", ondelete="CASCADE"),
            schema=schema,
        )
        print(f"[001_all_tables] ✓ wc_policy_officers")

    if not _exists(conn, schema, "wc_audit_cases"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".wc_audit_cases (
                id                     SERIAL PRIMARY KEY,
                policy_id              INTEGER NOT NULL REFERENCES "{schema}".wc_policies(id) ON DELETE CASCADE,
                audit_reference        VARCHAR(100) NOT NULL,
                status                 "{schema}".audit_status_enum NOT NULL DEFAULT 'pending',
                audit_period_start     DATE,
                audit_period_end       DATE,
                first_check_date       DATE,
                last_check_date        DATE,
                expected_submissions   FLOAT         DEFAULT 0.0,
                actual_submissions     FLOAT         DEFAULT 0.0,
                submitted_count        INTEGER       DEFAULT 0,
                total_earned_exposure  NUMERIC(15,2) DEFAULT 0.0,
                total_earned_premium   NUMERIC(15,2) DEFAULT 0.0,
                total_est_exposure     NUMERIC(15,2) DEFAULT 0.0,
                total_est_ytd_premium  NUMERIC(15,2) DEFAULT 0.0,
                total_variance         NUMERIC(15,2) DEFAULT 0.0,
                total_variance_pct     NUMERIC(8,4)  DEFAULT 0.0,
                ai_narrative           TEXT,
                risk_level             VARCHAR(20)   DEFAULT 'low',
                recommendation         "{schema}".recommendation_enum,
                hitl_required          BOOLEAN       DEFAULT FALSE,
                hitl_approved_by       VARCHAR(255),
                hitl_notes             TEXT,
                hitl_approved_at       TIMESTAMP,
                auditor_override       BOOLEAN       DEFAULT FALSE,
                auditor_notes          TEXT,
                auditor_id             VARCHAR(100),
                created_at             TIMESTAMP     DEFAULT NOW(),
                updated_at             TIMESTAMP     DEFAULT NOW(),
                completed_at           TIMESTAMP,
                payroll_file_path      VARCHAR(500),
                policy_xml_path        VARCHAR(500),
                audit_meta_file_path   VARCHAR(500),
                CONSTRAINT uq_{schema}_wcac_ref UNIQUE(audit_reference)
            );
            CREATE INDEX ix_{schema}_wcac_id ON "{schema}".wc_audit_cases(id);
        """))
        print(f"[001_all_tables] ✓ wc_audit_cases")

    if not _exists(conn, schema, "wc_payroll_records"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".wc_payroll_records (
                id              SERIAL PRIMARY KEY,
                audit_case_id   INTEGER NOT NULL REFERENCES "{schema}".wc_audit_cases(id) ON DELETE CASCADE,
                source          "{schema}".data_source_enum NOT NULL,
                client_name     VARCHAR(255),
                policy_number   VARCHAR(50) NOT NULL,
                check_date      DATE,
                ee_no           VARCHAR(50),
                employee_name   VARCHAR(255),
                state_code      VARCHAR(5),
                class_code      VARCHAR(10),
                wages           NUMERIC(15,2) DEFAULT 0.0,
                overtime_pay    NUMERIC(15,2) DEFAULT 0.0,
                double_time     NUMERIC(15,2) DEFAULT 0.0,
                tips            NUMERIC(15,2) DEFAULT 0.0,
                net_pay         NUMERIC(15,2) DEFAULT 0.0,
                exposure        NUMERIC(15,2) DEFAULT 0.0,
                net_rate        NUMERIC(10,6) DEFAULT 0.0,
                earned_premium  NUMERIC(15,2) DEFAULT 0.0,
                census_rate     NUMERIC(10,6) DEFAULT 0.0,
                census_premium  NUMERIC(15,2) DEFAULT 0.0,
                pol_eff_date    DATE,
                process_date    DATE,
                created_at      TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX ix_{schema}_wcpr_id ON "{schema}".wc_payroll_records(id);
        """))
        print(f"[001_all_tables] ✓ wc_payroll_records")

    if not _exists(conn, schema, "wc_variance_lines"):
        conn.execute(sa.DDL(f"""
            CREATE TABLE "{schema}".wc_variance_lines (
                id                SERIAL PRIMARY KEY,
                audit_case_id     INTEGER NOT NULL REFERENCES "{schema}".wc_audit_cases(id) ON DELETE CASCADE,
                policy_number     VARCHAR(50),
                state_code        VARCHAR(5),
                class_code        VARCHAR(10),
                class_desc        VARCHAR(255),
                earned_exposure   NUMERIC(15,2) DEFAULT 0.0,
                earned_premium    NUMERIC(15,2) DEFAULT 0.0,
                est_exposure      NUMERIC(15,2) DEFAULT 0.0,
                est_ytd_premium   NUMERIC(15,2) DEFAULT 0.0,
                variance          NUMERIC(15,2) DEFAULT 0.0,
                variance_pct      NUMERIC(8,4)  DEFAULT 0.0,
                root_cause        "{schema}".variance_root_cause DEFAULT 'none',
                root_cause_detail TEXT,
                is_flagged        BOOLEAN DEFAULT FALSE,
                flag_reason       TEXT,
                created_at        TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX ix_{schema}_wcvl_id ON "{schema}".wc_variance_lines(id);
        """))
        print(f"[001_all_tables] ✓ wc_variance_lines")

    if not _exists(conn, schema, "wc_agent_findings"):
        op.create_table(
            "wc_agent_findings",
            sa.Column("id",            sa.Integer(),    nullable=False),
            sa.Column("audit_case_id", sa.Integer(),    nullable=False),
            sa.Column("agent_name",    sa.String(100),  nullable=False),
            sa.Column("finding_type",  sa.String(100)),
            sa.Column("severity",      sa.String(20),   server_default="info"),
            sa.Column("summary",       sa.Text()),
            sa.Column("detail",        postgresql.JSONB()),
            sa.Column("evidence_ref",  sa.Text()),
            sa.Column("created_at",    sa.DateTime(),   server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["audit_case_id"], [f'{schema}.wc_audit_cases.id'],
                                    name=f"fk_{schema}_wcaf_case", ondelete="CASCADE"),
            schema=schema,
        )
        print(f"[001_all_tables] ✓ wc_agent_findings")

    if not _exists(conn, schema, "wc_hitl_reviews"):
        op.create_table(
            "wc_hitl_reviews",
            sa.Column("id",            sa.Integer(),    nullable=False),
            sa.Column("audit_case_id", sa.Integer(),    nullable=False),
            sa.Column("reviewer_id",   sa.String(100)),
            sa.Column("reviewer_name", sa.String(255)),
            sa.Column("action",        sa.String(50)),
            sa.Column("notes",         sa.Text()),
            sa.Column("override_data", postgresql.JSONB()),
            sa.Column("reviewed_at",   sa.DateTime(),   server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["audit_case_id"], [f'{schema}.wc_audit_cases.id'],
                                    name=f"fk_{schema}_wchr_case", ondelete="CASCADE"),
            schema=schema,
        )
        print(f"[001_all_tables] ✓ wc_hitl_reviews")

    if not _exists(conn, schema, "wc_audit_reports"):
        op.create_table(
            "wc_audit_reports",
            sa.Column("id",            sa.Integer(),    nullable=False),
            sa.Column("audit_case_id", sa.Integer(),    nullable=False),
            sa.Column("report_ref",    sa.String(100)),
            sa.Column("generated_at",  sa.DateTime(),   server_default=sa.text("now()")),
            sa.Column("report_json",   postgresql.JSONB()),
            sa.Column("report_file",   sa.String(500)),
            sa.Column("summary",       sa.Text()),
            sa.Column("is_final",      sa.Boolean(),    server_default=sa.text("false")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("audit_case_id", name=f"uq_{schema}_wcar_case"),
            sa.UniqueConstraint("report_ref",    name=f"uq_{schema}_wcar_ref"),
            sa.ForeignKeyConstraint(["audit_case_id"], [f'{schema}.wc_audit_cases.id'],
                                    name=f"fk_{schema}_wcar_case", ondelete="CASCADE"),
            schema=schema,
        )
        print(f"[001_all_tables] ✓ wc_audit_reports")

    # =========================================================================
    # TRIGGERS — auto-update updated_at
    # =========================================================================
    conn.execute(sa.DDL(f"""
        CREATE OR REPLACE FUNCTION "{schema}".update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END;
        $$ language 'plpgsql';
    """))
    for tbl in ["users","agents","hitl_records","agent_builder_configs",
                "agent_execution_triggers","agent_variables","wc_audit_cases"]:
        conn.execute(sa.DDL(f"""
            DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON "{schema}".{tbl};
            CREATE TRIGGER trg_{tbl}_updated_at
            BEFORE UPDATE ON "{schema}".{tbl}
            FOR EACH ROW EXECUTE FUNCTION "{schema}".update_updated_at_column();
        """))

    print(f"[001_all_tables] ✅ All tables created in schema: {schema}")


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    schema = _s()
    conn = op.get_bind()
    print(f"[001_all_tables] Running downgrade for schema: {schema}")

    # Drop in reverse dependency order
    for tbl in [
        "wc_audit_reports","wc_hitl_reviews","wc_agent_findings",
        "wc_variance_lines","wc_payroll_records","wc_audit_cases",
        "wc_policy_officers","wc_policy_class_codes","wc_policies",
        "computational_audit_usage","agent_versions","agent_variables",
        "agent_execution_triggers","agent_builder_configs",
        "hitl_records","agent_execution_logs","agents",
        "tool_registry","api_configurations","database_connections",
        "agent_templates","model_pricing","ai_models",
        "sso_configurations","workflow_templates","notifications",
        "audit_logs","users","tenants",
    ]:
        conn.execute(text(f'DROP TABLE IF EXISTS "{schema}".{tbl} CASCADE'))

    for enum_name in ["audit_status_enum","variance_root_cause",
                      "recommendation_enum","data_source_enum"]:
        conn.execute(text(f'DROP TYPE IF EXISTS "{schema}".{enum_name} CASCADE'))

    conn.execute(text(f'DROP FUNCTION IF EXISTS "{schema}".update_updated_at_column() CASCADE'))
    print(f"[001_all_tables] ✅ Downgrade complete for schema: {schema}")