"""create agent builder tenant tables - COMPLETE VERSION"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from sqlalchemy.dialects import postgresql

revision = "202502_tenant"
down_revision = "cc968bca1084"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ============================================================================
    # 1. AGENT BUILDER CONFIGS - COMPLETE VERSION WITH ALL COLUMNS
    # ============================================================================
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS agent_builder_configs (
        id SERIAL PRIMARY KEY,
        agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
        
        -- LLM Configuration (ALL FIELDS)
        llm_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
        llm_model VARCHAR(100) NOT NULL DEFAULT 'gpt-4',
        llm_temperature DECIMAL(3,2) DEFAULT 0.7,
        llm_max_tokens INTEGER DEFAULT 2000,
        llm_api_endpoint TEXT,
        llm_api_key_ref VARCHAR(255),
        
        -- Input Configuration
        input_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
        input_preprocessing JSONB DEFAULT '[]'::jsonb,
        input_validation_rules JSONB DEFAULT '{}'::jsonb,
        
        -- Tool Configuration
        enabled_tools JSONB NOT NULL DEFAULT '[]'::jsonb,
        tool_timeout_seconds INTEGER DEFAULT 300,
        max_tool_calls INTEGER DEFAULT 10,
        
        -- Database Integration
        db_connection_id INTEGER,
        db_queries JSONB DEFAULT '[]'::jsonb,
        db_write_enabled BOOLEAN DEFAULT FALSE,
        
        -- API Integration
        api_endpoints JSONB DEFAULT '[]'::jsonb,
        api_auth_method VARCHAR(50),
        api_rate_limit INTEGER,
        
        -- Data Source Configuration
        data_sources JSONB DEFAULT '[]'::jsonb,
        data_refresh_interval INTEGER,
        
        -- Output Configuration
        output_format VARCHAR(50) NOT NULL DEFAULT 'json',
        output_destination JSONB NOT NULL DEFAULT '{}'::jsonb,
        output_schema JSONB DEFAULT '{}'::jsonb,
        output_transformation JSONB DEFAULT '{}'::jsonb,
        
        -- LangGraph Orchestration
        trigger_type VARCHAR(50) NOT NULL DEFAULT 'manual',
        trigger_config JSONB DEFAULT '{}'::jsonb,
        schedule_cron VARCHAR(100),
        event_listeners JSONB DEFAULT '[]'::jsonb,
        
        -- HITL Configuration
        hitl_enabled BOOLEAN NOT NULL DEFAULT FALSE,
        hitl_trigger_conditions JSONB DEFAULT '{}'::jsonb,
        hitl_approval_required BOOLEAN DEFAULT FALSE,
        hitl_timeout_minutes INTEGER DEFAULT 60,
        hitl_escalation_rules JSONB DEFAULT '{}'::jsonb,
        
        -- Workflow Control
        max_execution_time_seconds INTEGER DEFAULT 3600,
        retry_policy JSONB DEFAULT '{"max_retries": 3, "backoff_multiplier": 2}'::jsonb,
        error_handling_strategy VARCHAR(50) DEFAULT 'fail',
        
        -- Conditional Logic
        conditional_branches JSONB DEFAULT '[]'::jsonb,
        loop_configuration JSONB DEFAULT '{}'::jsonb,
        parallel_execution_enabled BOOLEAN DEFAULT FALSE,
        
        -- Monitoring & Logging
        logging_level VARCHAR(20) DEFAULT 'INFO',
        metrics_enabled BOOLEAN DEFAULT TRUE,
        alert_rules JSONB DEFAULT '[]'::jsonb,
        
        -- Version Control
        version INTEGER NOT NULL DEFAULT 1,
        change_log TEXT,
        
        -- Timestamps
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        UNIQUE(agent_id, version)
    );
    """))

    # Create index for faster lookups
    conn.execute(text("""
    CREATE INDEX IF NOT EXISTS idx_agent_builder_configs_agent_id 
    ON agent_builder_configs(agent_id);
    """))

    # ============================================================================
    # 2. AGENT EXECUTION TRIGGERS - COMPLETE VERSION
    # ============================================================================
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS agent_execution_triggers (
        id SERIAL PRIMARY KEY,
        agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
        
        -- Trigger configuration
        trigger_name VARCHAR(255) NOT NULL,
        trigger_type VARCHAR(50) NOT NULL,
        
        -- Trigger conditions
        conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
        filters JSONB DEFAULT '{}'::jsonb,
        
        -- Webhook configuration
        webhook_url TEXT,
        webhook_secret VARCHAR(255),
        webhook_method VARCHAR(10) DEFAULT 'POST',
        
        -- Schedule configuration
        cron_expression VARCHAR(100),
        timezone VARCHAR(50) DEFAULT 'UTC',
        
        -- Status
        is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
        last_triggered TIMESTAMP WITH TIME ZONE,
        trigger_count INTEGER DEFAULT 0,
        
        -- Timestamps
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT valid_trigger_type CHECK (
            trigger_type IN ('scheduled', 'webhook', 'event', 'manual', 'file_upload', 'database_change', 'api_call')
        )
    );
    """))

    conn.execute(text("""
    CREATE INDEX IF NOT EXISTS idx_agent_execution_triggers_agent_id 
    ON agent_execution_triggers(agent_id);
    """))

    # ============================================================================
    # 3. AGENT VARIABLES - COMPLETE VERSION
    # ============================================================================
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS agent_variables (
        id SERIAL PRIMARY KEY,
        agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
        
        -- Variable details
        variable_name VARCHAR(255) NOT NULL,
        variable_type VARCHAR(50) NOT NULL,
        variable_value TEXT,
        encrypted_value TEXT,
        
        -- Metadata
        description TEXT,
        is_secret BOOLEAN NOT NULL DEFAULT FALSE,
        is_required BOOLEAN NOT NULL DEFAULT FALSE,
        default_value TEXT,
        
        -- Scope
        scope VARCHAR(50) NOT NULL DEFAULT 'agent',
        
        -- Timestamps
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        UNIQUE(agent_id, variable_name),
        
        CONSTRAINT valid_variable_type CHECK (
            variable_type IN ('string', 'number', 'boolean', 'secret', 'json', 'array')
        )
    );
    """))

    conn.execute(text("""
    CREATE INDEX IF NOT EXISTS idx_agent_variables_agent_id 
    ON agent_variables(agent_id);
    """))

    # ============================================================================
    # 4. AGENT VERSIONS - COMPLETE VERSION
    # ============================================================================
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS agent_versions (
        id SERIAL PRIMARY KEY,
        agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
        
        -- Version info
        version_number INTEGER NOT NULL,
        version_tag VARCHAR(50),
        
        -- Snapshot of configuration
        config_snapshot JSONB NOT NULL,
        builder_config_snapshot JSONB,
        
        -- Changes
        change_description TEXT,
        changed_by INTEGER,
        
        -- Status
        is_deployed BOOLEAN NOT NULL DEFAULT FALSE,
        deployed_at TIMESTAMP WITH TIME ZONE,
        
        -- Timestamp
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        
        UNIQUE(agent_id, version_number)
    );
    """))

    conn.execute(text("""
    CREATE INDEX IF NOT EXISTS idx_agent_versions_agent_id 
    ON agent_versions(agent_id);
    """))

    # ============================================================================
    # 5. CREATE UPDATE TRIGGERS
    # ============================================================================
    conn.execute(text("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """))

    # Add update triggers for tables with updated_at column
    for table in ['agent_builder_configs', 'agent_execution_triggers', 'agent_variables']:
        conn.execute(text(f"""
        DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
        CREATE TRIGGER update_{table}_updated_at 
        BEFORE UPDATE ON {table}
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """))


def downgrade():
    conn = op.get_bind()
    
    # Drop triggers first
    for table in ['agent_builder_configs', 'agent_execution_triggers', 'agent_variables']:
        conn.execute(text(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}"))
    
    # Drop tables
    conn.execute(text("DROP TABLE IF EXISTS agent_versions CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS agent_variables CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS agent_execution_triggers CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS agent_builder_configs CASCADE"))
    
    # Drop function
    conn.execute(text("DROP FUNCTION IF EXISTS update_updated_at_column()"))