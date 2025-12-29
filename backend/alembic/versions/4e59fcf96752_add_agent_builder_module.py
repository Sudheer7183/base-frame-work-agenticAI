"""create agent builder core (public schema)"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from sqlalchemy.dialects import postgresql

revision = "202501_pub"
down_revision = "cc968bca1084"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # agent_templates
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS public.agent_templates (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        description TEXT,
        category VARCHAR(100) NOT NULL,
        icon VARCHAR(50),
        template_config JSONB NOT NULL DEFAULT '{}'::jsonb,
        default_tools JSONB NOT NULL DEFAULT '[]'::jsonb,
        required_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
        workflow_type VARCHAR(100) NOT NULL,
        node_configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
        is_official BOOLEAN NOT NULL DEFAULT FALSE,
        is_public BOOLEAN NOT NULL DEFAULT TRUE,
        created_by INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_agent_templates_category ON public.agent_templates(category);
    CREATE INDEX IF NOT EXISTS idx_agent_templates_workflow ON public.agent_templates(workflow_type);
    """))

    # database_connections
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS public.database_connections (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        db_type VARCHAR(50) NOT NULL,
        host VARCHAR(255),
        port INTEGER,
        database_name VARCHAR(255),
        username VARCHAR(255),
        password_encrypted TEXT,
        connection_string_template TEXT,
        pool_size INTEGER DEFAULT 5,
        max_overflow INTEGER DEFAULT 10,
        pool_timeout INTEGER DEFAULT 30,
        ssl_enabled BOOLEAN DEFAULT TRUE,
        ssl_cert TEXT,
        created_by INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
        allowed_operations JSONB DEFAULT '["read"]'::jsonb,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        last_tested TIMESTAMP WITH TIME ZONE,
        last_test_status VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """))

    # api_configurations
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS public.api_configurations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        base_url TEXT NOT NULL,
        api_version VARCHAR(50),
        auth_type VARCHAR(50) NOT NULL,
        auth_credentials JSONB NOT NULL DEFAULT '{}'::jsonb,
        oauth_config JSONB,
        rate_limit_per_minute INTEGER,
        rate_limit_per_hour INTEGER,
        default_headers JSONB DEFAULT '{}'::jsonb,
        timeout_seconds INTEGER DEFAULT 30,
        retry_config JSONB DEFAULT '{"max_retries": 3, "backoff": "exponential"}'::jsonb,
        documentation_url TEXT,
        example_requests JSONB DEFAULT '[]'::jsonb,
        created_by INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """))

    # tool_registry
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS public.tool_registry (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        display_name VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        tool_type VARCHAR(50) NOT NULL,
        category VARCHAR(100) NOT NULL,
        implementation_type VARCHAR(50) NOT NULL,
        code_reference TEXT,
        input_schema JSONB NOT NULL,
        output_schema JSONB NOT NULL,
        parameter_hints JSONB DEFAULT '{}'::jsonb,
        requires_auth BOOLEAN DEFAULT FALSE,
        required_permissions JSONB DEFAULT '[]'::jsonb,
        cost_per_call DECIMAL(10,4) DEFAULT 0,
        avg_execution_time_ms INTEGER,
        timeout_seconds INTEGER DEFAULT 30,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        is_premium BOOLEAN NOT NULL DEFAULT FALSE,
        version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
        author VARCHAR(255),
        documentation_url TEXT,
        example_usage JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """))

    # update_updated_at_column() function
    conn.execute(text("""
    CREATE OR REPLACE FUNCTION public.update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END;
    $$ language 'plpgsql';
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS public.agent_templates CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS public.database_connections CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS public.api_configurations CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS public.tool_registry CASCADE"))
    conn.execute(text("DROP FUNCTION IF EXISTS public.update_updated_at_column() CASCADE"))
