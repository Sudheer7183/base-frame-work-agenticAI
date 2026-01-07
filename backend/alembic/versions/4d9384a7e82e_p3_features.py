"""
Add P3 features tables

Revision ID: 004_add_p3_features
Revises: 003_add_users
Create Date: 2024-12-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d9384a7e82e'
down_revision: Union[str, None] = '514d33145663'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add tables for P3 features: Workflow Marketplace, SSO, Analytics, AI Model Management
    
    Tables are created in the public schema (system-wide) or tenant schemas (tenant-specific)
    based on their purpose.
    """
    
    # =========================================================================
    # PUBLIC SCHEMA TABLES (System-wide, no tenant isolation)
    # =========================================================================
    
    # -------------------------------------------------------------------------
    # 1. WORKFLOW MARKETPLACE TEMPLATES (Public - shared across tenants)
    # -------------------------------------------------------------------------
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    public_tables = inspector.get_table_names(schema='public')

    # Check if ALL expected tables exist
    expected_tables = ['workflow_templates', 'sso_configurations', 'ai_models']
    if all(table in public_tables for table in expected_tables):
        print(f"[Migration {revision}] All tables already exist, skipping")
        return

    

    op.create_table(
        'workflow_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('workflow_definition', postgresql.JSONB(), nullable=False),
        sa.Column('config_schema', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('author_id', sa.Integer(), nullable=True),  # Reference to user, but stored globally
        sa.Column('author_tenant', sa.String(100), nullable=True),  # Store tenant slug for context
        sa.Column('is_official', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('install_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rating', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    op.create_index('idx_workflow_templates_name', 'workflow_templates', ['name'], schema='public')
    op.create_index('idx_workflow_templates_category', 'workflow_templates', ['category'], schema='public')
    op.create_index('idx_workflow_templates_is_official', 'workflow_templates', ['is_official'], schema='public')
    op.create_index('idx_workflow_templates_is_public', 'workflow_templates', ['is_public'], schema='public')
    
    # -------------------------------------------------------------------------
    # 2. SSO CONFIGURATIONS (Public - system-wide SSO settings)
    # -------------------------------------------------------------------------
    
    op.create_table(
        'sso_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_slug', sa.String(100), nullable=False),
        sa.Column('provider_type', sa.String(50), nullable=False),
        sa.Column('provider_name', sa.String(255), nullable=False),
        sa.Column('client_id', sa.String(500), nullable=True),
        sa.Column('client_secret', sa.Text(), nullable=True),
        sa.Column('authorization_endpoint', sa.String(500), nullable=True),
        sa.Column('token_endpoint', sa.String(500), nullable=True),
        sa.Column('userinfo_endpoint', sa.String(500), nullable=True),
        sa.Column('jwks_uri', sa.String(500), nullable=True),
        sa.Column('saml_entity_id', sa.String(500), nullable=True),
        sa.Column('saml_sso_url', sa.String(500), nullable=True),
        sa.Column('saml_certificate', sa.Text(), nullable=True),
        sa.Column('scopes', postgresql.JSONB(), nullable=False,
                  server_default='["openid", "email", "profile"]'),
        sa.Column('redirect_uri', sa.String(500), nullable=False),
        sa.Column('attribute_mapping', postgresql.JSONB(), nullable=False,
                  server_default='{"email": "email", "given_name": "first_name", "family_name": "last_name", "name": "full_name"}'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_provision_users', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('default_role', sa.String(100), nullable=True, server_default='user'),
        sa.Column('require_email_verification', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    op.create_index('idx_sso_configs_tenant', 'sso_configurations', ['tenant_slug'], schema='public')
    op.create_index('idx_sso_configs_enabled', 'sso_configurations', ['is_enabled'], schema='public')
    op.create_index('idx_sso_configs_tenant_provider', 'sso_configurations', 
                    ['tenant_slug', 'provider_type'], unique=True, schema='public')
    
    # -------------------------------------------------------------------------
    # 3. AI MODELS CATALOG (Public - available models for all tenants)
    # -------------------------------------------------------------------------
    
    op.create_table(
        'ai_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('model_id', sa.String(255), nullable=False, unique=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('capabilities', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('context_window', sa.Integer(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('input_cost_per_1m', sa.Float(), nullable=True),
        sa.Column('output_cost_per_1m', sa.Float(), nullable=True),
        sa.Column('avg_latency_ms', sa.Float(), nullable=True),
        sa.Column('throughput_tokens_per_sec', sa.Float(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('default_parameters', postgresql.JSONB(), nullable=False,
                  server_default='{"temperature": 0.7, "max_tokens": 1000, "top_p": 1.0}'),
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    op.create_index('idx_ai_models_name', 'ai_models', ['name'], schema='public')
    op.create_index('idx_ai_models_provider', 'ai_models', ['provider'], schema='public')
    op.create_index('idx_ai_models_status', 'ai_models', ['status'], schema='public')
    op.create_index('idx_ai_models_enabled', 'ai_models', ['is_enabled'], schema='public')
    
    # =========================================================================
    # TENANT SCHEMA TABLES (Created via SQL function for each tenant)
    # =========================================================================
    
    # Create a SQL function that will add P3 tables to tenant schemas
    op.execute("""
    CREATE OR REPLACE FUNCTION create_p3_tenant_tables(tenant_schema TEXT)
    RETURNS void AS $$
    BEGIN
        -- Set search path to tenant schema
        EXECUTE format('SET search_path TO %I, public', tenant_schema);
        
        -- =====================================================================
        -- Workflow Reviews (tenant-specific)
        -- =====================================================================
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.workflow_reviews (
                id SERIAL PRIMARY KEY,
                template_id INTEGER NOT NULL,  -- References public.workflow_templates
                user_id INTEGER NOT NULL,      -- References tenant users table
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                helpful_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES %I.users(id) ON DELETE CASCADE
            )', tenant_schema, tenant_schema);
        
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_workflow_reviews_template ON %I.workflow_reviews(template_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_workflow_reviews_user ON %I.workflow_reviews(user_id)', tenant_schema);
        
        -- =====================================================================
        -- Workflow Installations (tenant-specific)
        -- =====================================================================
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.workflow_installations (
                id SERIAL PRIMARY KEY,
                template_id INTEGER NOT NULL,  -- References public.workflow_templates
                user_id INTEGER NOT NULL,      -- References tenant users table
                agent_id INTEGER,              -- References tenant agents table
                customizations JSONB NOT NULL DEFAULT ''{}''::jsonb,
                is_active BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES %I.users(id) ON DELETE CASCADE,
                FOREIGN KEY (agent_id) REFERENCES %I.agents(id) ON DELETE SET NULL
            )', tenant_schema, tenant_schema, tenant_schema);
        
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_workflow_installations_template ON %I.workflow_installations(template_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_workflow_installations_user ON %I.workflow_installations(user_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_workflow_installations_agent ON %I.workflow_installations(agent_id)', tenant_schema);
        
        -- =====================================================================
        -- SSO Sessions (tenant-specific)
        -- =====================================================================
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.sso_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                tenant_slug VARCHAR(100) NOT NULL,
                provider_type VARCHAR(50) NOT NULL,
                sso_user_id VARCHAR(500) NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                id_token TEXT,
                expires_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES %I.users(id) ON DELETE CASCADE
            )', tenant_schema, tenant_schema);
        
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_sso_sessions_user ON %I.sso_sessions(user_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_sso_sessions_sso_user ON %I.sso_sessions(sso_user_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_sso_sessions_expires ON %I.sso_sessions(expires_at)', tenant_schema);
        
        -- =====================================================================
        -- Analytics Events (tenant-specific)
        -- =====================================================================
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.analytics_events (
                id SERIAL PRIMARY KEY,
                tenant_slug VARCHAR(100) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INTEGER NOT NULL,
                user_id INTEGER,
                agent_id INTEGER,
                properties JSONB NOT NULL DEFAULT ''{}''::jsonb,
                value DOUBLE PRECISION,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES %I.users(id) ON DELETE SET NULL,
                FOREIGN KEY (agent_id) REFERENCES %I.agents(id) ON DELETE SET NULL
            )', tenant_schema, tenant_schema, tenant_schema);
        
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON %I.analytics_events(event_type)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_analytics_events_entity ON %I.analytics_events(entity_type, entity_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON %I.analytics_events(timestamp)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_analytics_events_user ON %I.analytics_events(user_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_analytics_events_agent ON %I.analytics_events(agent_id)', tenant_schema);
        
        -- =====================================================================
        -- Analytics Aggregates (tenant-specific)
        -- =====================================================================
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.analytics_aggregates (
                id SERIAL PRIMARY KEY,
                tenant_slug VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INTEGER NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                granularity VARCHAR(20) NOT NULL,
                period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                sum_value DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                avg_value DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                min_value DOUBLE PRECISION,
                max_value DOUBLE PRECISION,
                percentile_50 DOUBLE PRECISION,
                percentile_95 DOUBLE PRECISION,
                percentile_99 DOUBLE PRECISION,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            )', tenant_schema);
        
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_analytics_agg_entity ON %I.analytics_aggregates(entity_type, entity_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_analytics_agg_metric ON %I.analytics_aggregates(metric_type)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_analytics_agg_period ON %I.analytics_aggregates(period_start)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_analytics_agg_granularity ON %I.analytics_aggregates(granularity)', tenant_schema);
        
        -- =====================================================================
        -- Model Configurations (tenant-specific)
        -- =====================================================================
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.model_configurations (
                id SERIAL PRIMARY KEY,
                tenant_slug VARCHAR(100) NOT NULL,
                model_id INTEGER NOT NULL,  -- References public.ai_models
                agent_id INTEGER,           -- References tenant agents table
                parameters JSONB NOT NULL DEFAULT ''{}''::jsonb,
                api_endpoint VARCHAR(500),
                api_key_encrypted TEXT,
                max_requests_per_minute INTEGER,
                max_tokens_per_day INTEGER,
                fallback_model_id INTEGER,  -- References public.ai_models
                retry_attempts INTEGER NOT NULL DEFAULT 3,
                is_active BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES %I.agents(id) ON DELETE CASCADE
            )', tenant_schema, tenant_schema);
        
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_model_configs_model ON %I.model_configurations(model_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_model_configs_agent ON %I.model_configurations(agent_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_model_configs_active ON %I.model_configurations(is_active)', tenant_schema);
        
        -- =====================================================================
        -- Model Usage (tenant-specific)
        -- =====================================================================
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.model_usage (
                id SERIAL PRIMARY KEY,
                tenant_slug VARCHAR(100) NOT NULL,
                model_id INTEGER NOT NULL,  -- References public.ai_models
                agent_id INTEGER,           -- References tenant agents table
                execution_id VARCHAR(255),
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                latency_ms DOUBLE PRECISION,
                success BOOLEAN NOT NULL DEFAULT true,
                error_message VARCHAR(500),
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES %I.agents(id) ON DELETE SET NULL
            )', tenant_schema, tenant_schema);
        
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_model_usage_model ON %I.model_usage(model_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_model_usage_agent ON %I.model_usage(agent_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_model_usage_execution ON %I.model_usage(execution_id)', tenant_schema);
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_model_usage_timestamp ON %I.model_usage(timestamp)', tenant_schema);
        
        -- Reset search path
        EXECUTE 'SET search_path TO public';
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Apply P3 tables to all existing tenant schemas
    op.execute("""
    DO $$
    DECLARE
        tenant_record RECORD;
    BEGIN
        -- Find all tenant schemas (schemas that are not system schemas)
        FOR tenant_record IN 
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast')
            AND schema_name NOT LIKE 'pg_%'
        LOOP
            -- Create P3 tables in each tenant schema
            RAISE NOTICE 'Creating P3 tables in schema: %', tenant_record.schema_name;
            PERFORM create_p3_tenant_tables(tenant_record.schema_name);
        END LOOP;
    END $$;
    """)


def downgrade() -> None:
    """Drop P3 features tables"""
    
    # Drop the tenant table creation function
    op.execute("DROP FUNCTION IF EXISTS create_p3_tenant_tables(TEXT)")
    
    # Drop tenant-specific tables from all tenant schemas
    op.execute("""
    DO $$
    DECLARE
        tenant_record RECORD;
    BEGIN
        FOR tenant_record IN 
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('public', 'information_schema', 'pg_catalog', 'pg_toast')
            AND schema_name NOT LIKE 'pg_%'
        LOOP
            EXECUTE format('DROP TABLE IF EXISTS %I.model_usage CASCADE', tenant_record.schema_name);
            EXECUTE format('DROP TABLE IF EXISTS %I.model_configurations CASCADE', tenant_record.schema_name);
            EXECUTE format('DROP TABLE IF EXISTS %I.analytics_aggregates CASCADE', tenant_record.schema_name);
            EXECUTE format('DROP TABLE IF EXISTS %I.analytics_events CASCADE', tenant_record.schema_name);
            EXECUTE format('DROP TABLE IF EXISTS %I.sso_sessions CASCADE', tenant_record.schema_name);
            EXECUTE format('DROP TABLE IF EXISTS %I.workflow_installations CASCADE', tenant_record.schema_name);
            EXECUTE format('DROP TABLE IF EXISTS %I.workflow_reviews CASCADE', tenant_record.schema_name);
        END LOOP;
    END $$;
    """)
    
    # Drop public schema tables
    op.drop_table('ai_models', schema='public')
    op.drop_table('sso_configurations', schema='public')
    op.drop_table('workflow_templates', schema='public')


