"""computational audit tables

Revision ID: 57ec5ea850a8
Revises: 202502_tenant
Create Date: 2025-12-31 11:29:10.870361

"""
from typing import Sequence, Union
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = '57ec5ea850a8'
down_revision: Union[str, None] = '202502_tenant'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """
    Create computational audit tables
    
    CRITICAL: This migration handles TWO different schema contexts:
    1. PUBLIC schema: Creates model_pricing table and helper functions
    2. TENANT schemas: Creates computational audit tables with proper FKs
    """
    
    # Get the current schema context from Alembic
    conn = op.get_bind()
    schema = context.get_context().version_table_schema
    
    print(f"[Migration {revision}] Running for schema: {schema or 'public'}")
    
    # =========================================================================
    # PART 1: PUBLIC SCHEMA ONLY - Model Pricing Table
    # =========================================================================
    if not schema or schema == "public":
        print(f"[Migration {revision}] Creating public.model_pricing table...")
        
        # Check if table already exists
        inspector = sa.inspect(conn)
        if 'model_pricing' not in inspector.get_table_names(schema='public'):
            conn.execute(text("""
                CREATE TABLE public.model_pricing (
                    id SERIAL PRIMARY KEY,
                    model_provider VARCHAR(50) NOT NULL,
                    model_name VARCHAR(100) NOT NULL,
                    model_version VARCHAR(50),
                    input_cost_per_1k NUMERIC(12,8) NOT NULL,
                    output_cost_per_1k NUMERIC(12,8) NOT NULL,
                    cache_read_per_1k NUMERIC(12,8) DEFAULT 0,
                    cache_write_per_1k NUMERIC(12,8) DEFAULT 0,
                    effective_from TIMESTAMP NOT NULL DEFAULT NOW(),
                    effective_until TIMESTAMP,
                    currency VARCHAR(3) DEFAULT 'USD',
                    active BOOLEAN DEFAULT TRUE,
                    notes VARCHAR(500),
                    source_url VARCHAR(500),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                -- Indexes for model_pricing
                CREATE INDEX idx_model_pricing_provider_name 
                    ON public.model_pricing(model_provider, model_name);
                CREATE INDEX idx_model_pricing_active 
                    ON public.model_pricing(active);
                CREATE INDEX idx_model_pricing_effective 
                    ON public.model_pricing(effective_from, effective_until);
                    
                COMMENT ON TABLE public.model_pricing IS 'Centralized LLM model pricing (shared across tenants)';
            """))
            print(f"[Migration {revision}] ✓ Created public.model_pricing table")
        else:
            print(f"[Migration {revision}] ℹ public.model_pricing already exists, skipping")
        
        # =====================================================================
        # Create PL/pgSQL function for tenant table generation
        # =====================================================================
        print(f"[Migration {revision}] Creating tenant table generation function...")
        
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION create_tenant_computational_tables(schema_name TEXT)
            RETURNS void AS $$
            BEGIN
                -- ============================================================
                -- Create computational_audit_usage table
                -- ============================================================
                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS %I.computational_audit_usage (
                        id SERIAL PRIMARY KEY,
                        execution_id VARCHAR(255) NOT NULL,
                        agent_id INTEGER NOT NULL,
                        stage_name VARCHAR(100) NOT NULL,
                        step_number INTEGER,
                        node_name VARCHAR(100),
                        model_provider VARCHAR(50) NOT NULL,
                        model_name VARCHAR(100) NOT NULL,
                        model_version VARCHAR(50),
                        input_tokens INTEGER DEFAULT 0,
                        output_tokens INTEGER DEFAULT 0,
                        cache_read_tokens INTEGER DEFAULT 0,
                        cache_write_tokens INTEGER DEFAULT 0,
                        total_tokens INTEGER DEFAULT 0,
                        unit_cost_input NUMERIC(12,8) NOT NULL,
                        unit_cost_output NUMERIC(12,8) NOT NULL,
                        computed_cost_usd NUMERIC(16,8) NOT NULL,
                        latency_ms INTEGER,
                        ttft_ms INTEGER,
                        retry_count INTEGER DEFAULT 0,
                        retry_reason VARCHAR(255),
                        tool_calls_count INTEGER DEFAULT 0,
                        tool_calls_data JSONB,
                        prompt_hash VARCHAR(64),
                        prompt_template_id VARCHAR(100),
                        finish_reason VARCHAR(50),
                        model_metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )', schema_name);
                
                -- Add foreign keys ONLY if parent tables exist
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = schema_name 
                    AND table_name = 'agent_execution_logs'
                ) THEN
                    EXECUTE format('
                        ALTER TABLE %I.computational_audit_usage
                        ADD CONSTRAINT fk_usage_execution
                        FOREIGN KEY (execution_id) 
                        REFERENCES %I.agent_execution_logs(execution_id) 
                        ON DELETE CASCADE
                    ', schema_name, schema_name);
                    RAISE NOTICE 'Added FK to agent_execution_logs for schema %', schema_name;
                END IF;
                
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = schema_name 
                    AND table_name = 'agents'
                ) THEN
                    EXECUTE format('
                        ALTER TABLE %I.computational_audit_usage
                        ADD CONSTRAINT fk_usage_agent
                        FOREIGN KEY (agent_id) 
                        REFERENCES %I.agents(id) 
                        ON DELETE CASCADE
                    ', schema_name, schema_name);
                    RAISE NOTICE 'Added FK to agents for schema %', schema_name;
                END IF;
                
                -- Create indexes
                EXECUTE format('
                    CREATE INDEX IF NOT EXISTS idx_usage_execution 
                        ON %I.computational_audit_usage(execution_id);
                    CREATE INDEX IF NOT EXISTS idx_usage_agent 
                        ON %I.computational_audit_usage(agent_id);
                    CREATE INDEX IF NOT EXISTS idx_usage_created 
                        ON %I.computational_audit_usage(created_at);
                    CREATE INDEX IF NOT EXISTS idx_usage_model 
                        ON %I.computational_audit_usage(model_provider, model_name);
                    CREATE INDEX IF NOT EXISTS idx_usage_cost 
                        ON %I.computational_audit_usage(computed_cost_usd)
                ', schema_name, schema_name, schema_name, schema_name, schema_name);
                
                EXECUTE format('
                    COMMENT ON TABLE %I.computational_audit_usage IS ''Tracks individual LLM calls with token counts and costs''
                ', schema_name);
                
                -- ============================================================
                -- Create computational_audit_cost_summary table
                -- ============================================================
                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS %I.computational_audit_cost_summary (
                        id SERIAL PRIMARY KEY,
                        execution_id VARCHAR(255) UNIQUE NOT NULL,
                        agent_id INTEGER NOT NULL,
                        total_llm_cost_usd NUMERIC(16,8) DEFAULT 0,
                        total_tokens INTEGER DEFAULT 0,
                        total_llm_calls INTEGER DEFAULT 0,
                        hitl_cost_usd NUMERIC(16,8) DEFAULT 0,
                        hitl_duration_seconds INTEGER DEFAULT 0,
                        infrastructure_cost_usd NUMERIC(16,8) DEFAULT 0,
                        total_cost_usd NUMERIC(16,8) DEFAULT 0,
                        execution_started_at TIMESTAMP,
                        execution_completed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )', schema_name);
                
                -- Create indexes
                EXECUTE format('
                    CREATE INDEX IF NOT EXISTS idx_summary_execution 
                        ON %I.computational_audit_cost_summary(execution_id);
                    CREATE INDEX IF NOT EXISTS idx_summary_agent 
                        ON %I.computational_audit_cost_summary(agent_id);
                    CREATE INDEX IF NOT EXISTS idx_summary_created 
                        ON %I.computational_audit_cost_summary(created_at);
                    CREATE INDEX IF NOT EXISTS idx_summary_cost 
                        ON %I.computational_audit_cost_summary(total_cost_usd);
                    CREATE INDEX IF NOT EXISTS idx_summary_dates 
                        ON %I.computational_audit_cost_summary(execution_started_at, execution_completed_at)
                ', schema_name, schema_name, schema_name, schema_name, schema_name);
                
                EXECUTE format('
                    COMMENT ON TABLE %I.computational_audit_cost_summary IS ''Aggregated cost summary per execution''
                ', schema_name);
                
                -- ============================================================
                -- Create tenant_pricing_config table
                -- ============================================================
                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS %I.tenant_pricing_config (
                        id SERIAL PRIMARY KEY,
                        pricing_tier VARCHAR(50) DEFAULT ''professional'',
                        monthly_token_quota INTEGER,
                        monthly_execution_quota INTEGER,
                        monthly_budget_usd NUMERIC(12,2),
                        overage_rate_per_1k_tokens NUMERIC(12,8),
                        overage_rate_multiplier NUMERIC(5,2) DEFAULT 1.5,
                        hitl_hourly_rate_usd NUMERIC(10,2) DEFAULT 50.00,
                        hitl_included_percent NUMERIC(5,2) DEFAULT 0,
                        cost_alert_threshold_usd NUMERIC(12,2),
                        token_alert_threshold INTEGER,
                        budget_alert_percentage NUMERIC(5,2) DEFAULT 80,
                        billing_cycle_day INTEGER DEFAULT 1,
                        billing_email VARCHAR(255),
                        self_hosted_gpu_type VARCHAR(50),
                        self_hosted_gpu_count INTEGER,
                        self_hosted_cost_per_hour NUMERIC(10,4),
                        active BOOLEAN DEFAULT TRUE,
                        custom_config JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )', schema_name);
                
                EXECUTE format('
                    COMMENT ON TABLE %I.tenant_pricing_config IS ''Tenant-specific pricing configuration and quotas''
                ', schema_name);
                
                RAISE NOTICE 'Created computational audit tables for schema: %', schema_name;
            END;
            $$ LANGUAGE plpgsql;
        """))
        print(f"[Migration {revision}] ✓ Created tenant table generation function")
        
        # =====================================================================
        # Apply to ALL existing tenant schemas
        # =====================================================================
        print(f"[Migration {revision}] Applying tables to existing tenant schemas...")
        
        conn.execute(text("""
            DO $$
            DECLARE
                tenant_record RECORD;
                schema_exists BOOLEAN;
            BEGIN
                -- Loop through all active tenants
                FOR tenant_record IN 
                    SELECT schema_name 
                    FROM public.tenants 
                    WHERE status = 'active'
                LOOP
                    -- Verify schema actually exists
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.schemata 
                        WHERE schema_name = tenant_record.schema_name
                    ) INTO schema_exists;
                    
                    IF schema_exists THEN
                        RAISE NOTICE 'Creating computational audit tables for tenant: %', tenant_record.schema_name;
                        PERFORM create_tenant_computational_tables(tenant_record.schema_name);
                    ELSE
                        RAISE WARNING 'Schema % does not exist, skipping', tenant_record.schema_name;
                    END IF;
                END LOOP;
                
                RAISE NOTICE 'Completed creating tables for all tenants';
            END $$;
        """))
        print(f"[Migration {revision}] ✓ Applied to all existing tenant schemas")
        
        # =====================================================================
        # Create trigger for automatic table creation on new tenants
        # =====================================================================
        print(f"[Migration {revision}] Creating auto-creation trigger...")
        
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION auto_create_computational_audit_tables()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.status = 'active' AND NEW.schema_name IS NOT NULL THEN
                    -- Check if schema exists
                    IF EXISTS(
                        SELECT 1 FROM information_schema.schemata 
                        WHERE schema_name = NEW.schema_name
                    ) THEN
                        PERFORM create_tenant_computational_tables(NEW.schema_name);
                        RAISE NOTICE 'Auto-created computational audit tables for new tenant: %', NEW.schema_name;
                    ELSE
                        RAISE WARNING 'Cannot create computational audit tables - schema % does not exist yet', NEW.schema_name;
                    END IF;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS trigger_create_computational_audit_tables ON public.tenants;
            
            CREATE TRIGGER trigger_create_computational_audit_tables
                AFTER INSERT OR UPDATE ON public.tenants
                FOR EACH ROW
                EXECUTE FUNCTION auto_create_computational_audit_tables();
        """))
        print(f"[Migration {revision}] ✓ Created auto-creation trigger")
        
        print(f"[Migration {revision}] ✅ PUBLIC schema migration completed successfully!")
    
    # =========================================================================
    # PART 2: TENANT SCHEMA - Apply computational audit tables
    # =========================================================================
    elif schema and schema != "public":
        print(f"[Migration {revision}] Creating computational audit tables in tenant schema: {schema}")
        
        # Call the function to create tables in this specific tenant schema
        conn.execute(text("""
            SELECT create_tenant_computational_tables(:schema_name)
        """), {"schema_name": schema})
        
        print(f"[Migration {revision}] ✅ TENANT schema migration completed for: {schema}")
    
    else:
        print(f"[Migration {revision}] ⚠ Unknown schema context, skipping")


def downgrade():
    """
    Remove computational audit tables
    
    WARNING: This will delete all cost tracking data!
    """
    
    conn = op.get_bind()
    schema = context.get_context().version_table_schema
    
    print(f"[Migration {revision}] ⚠️  Starting downgrade for schema: {schema or 'public'}")
    
    # =========================================================================
    # PART 1: PUBLIC SCHEMA - Drop functions, triggers, and model_pricing
    # =========================================================================
    if not schema or schema == "public":
        print(f"[Migration {revision}] Removing public schema objects...")
        
        # Drop trigger
        conn.execute(text("""
            DROP TRIGGER IF EXISTS trigger_create_computational_audit_tables ON public.tenants;
            DROP FUNCTION IF EXISTS auto_create_computational_audit_tables();
        """))
        
        # Drop tables from all tenant schemas
        conn.execute(text("""
            DO $$
            DECLARE
                tenant_record RECORD;
            BEGIN
                FOR tenant_record IN 
                    SELECT schema_name FROM public.tenants
                LOOP
                    EXECUTE format('DROP TABLE IF EXISTS %I.tenant_pricing_config CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.computational_audit_cost_summary CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.computational_audit_usage CASCADE', tenant_record.schema_name);
                    
                    RAISE NOTICE 'Dropped computational audit tables from schema: %', tenant_record.schema_name;
                END LOOP;
            END $$;
        """))
        
        # Drop helper function
        conn.execute(text("""
            DROP FUNCTION IF EXISTS create_tenant_computational_tables(TEXT);
        """))
        
        # Drop public.model_pricing
        conn.execute(text("""
            DROP TABLE IF EXISTS public.model_pricing CASCADE;
        """))
        
        print(f"[Migration {revision}] ✓ Removed public schema objects")
    
    # =========================================================================
    # PART 2: TENANT SCHEMA - Drop tenant-specific tables
    # =========================================================================
    elif schema and schema != "public":
        print(f"[Migration {revision}] Removing computational audit tables from: {schema}")
        
        conn.execute(text(f"""
            DROP TABLE IF EXISTS "{schema}".tenant_pricing_config CASCADE;
            DROP TABLE IF EXISTS "{schema}".computational_audit_cost_summary CASCADE;
            DROP TABLE IF EXISTS "{schema}".computational_audit_usage CASCADE;
        """))
        
        print(f"[Migration {revision}] ✓ Removed tables from {schema}")
    
    print(f"[Migration {revision}] ✅ Downgrade completed")


# END OF FILE - Migration complete (Fixed version with proper format() calls)