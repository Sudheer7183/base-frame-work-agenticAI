-- ============================================================================
-- AGENT BUILDER MODULE - DATABASE SCHEMA
-- ============================================================================
-- This schema extends the existing agent system with comprehensive configuration
-- capabilities for creating agents with UI-driven configuration
-- ============================================================================

-- ============================================================================
-- 1. AGENT TEMPLATES TABLE (Reusable agent configurations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100) NOT NULL, -- 'data_processing', 'api_integration', 'analytics', 'custom'
    icon VARCHAR(50), -- Icon identifier for UI
    
    -- Template configuration
    template_config JSONB NOT NULL DEFAULT '{}',
    default_tools JSONB NOT NULL DEFAULT '[]', -- List of default tool IDs
    required_fields JSONB NOT NULL DEFAULT '[]', -- Required configuration fields
    
    -- Workflow configuration
    workflow_type VARCHAR(100) NOT NULL, -- Maps to existing workflows
    node_configuration JSONB NOT NULL DEFAULT '{}', -- Custom node configs
    
    -- Metadata
    is_official BOOLEAN NOT NULL DEFAULT FALSE,
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_category CHECK (category IN ('data_processing', 'api_integration', 'analytics', 'ml_inference', 'custom', 'automation', 'monitoring'))
);

CREATE INDEX idx_agent_templates_category ON agent_templates(category);
CREATE INDEX idx_agent_templates_workflow ON agent_templates(workflow_type);

-- ============================================================================
-- 2. AGENT BUILDER CONFIGURATIONS (Extends agents table)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_builder_configs (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    
    -- LLM Configuration
    llm_provider VARCHAR(50) NOT NULL DEFAULT 'openai', -- 'openai', 'anthropic', 'ollama', 'azure'
    llm_model VARCHAR(100) NOT NULL DEFAULT 'gpt-4',
    llm_temperature DECIMAL(3,2) DEFAULT 0.7,
    llm_max_tokens INTEGER DEFAULT 2000,
    llm_api_endpoint TEXT, -- For custom endpoints
    llm_api_key_ref VARCHAR(255), -- Reference to secure key storage
    
    -- Input Configuration
    input_schema JSONB NOT NULL DEFAULT '{}', -- JSON Schema for validation
    input_preprocessing JSONB DEFAULT '[]', -- Preprocessing steps
    input_validation_rules JSONB DEFAULT '{}',
    
    -- Tool Configuration
    enabled_tools JSONB NOT NULL DEFAULT '[]', -- Array of tool configurations
    tool_timeout_seconds INTEGER DEFAULT 300,
    max_tool_calls INTEGER DEFAULT 10,
    
    -- Database Integration
    db_connection_id INTEGER REFERENCES database_connections(id) ON DELETE SET NULL,
    db_queries JSONB DEFAULT '[]', -- Predefined queries
    db_write_enabled BOOLEAN DEFAULT FALSE,
    
    -- API Integration
    api_endpoints JSONB DEFAULT '[]', -- External API configurations
    api_auth_method VARCHAR(50), -- 'api_key', 'oauth', 'basic', 'bearer'
    api_rate_limit INTEGER,
    
    -- Data Source Configuration
    data_sources JSONB DEFAULT '[]', -- CSV, Excel, JSON sources
    data_refresh_interval INTEGER, -- Seconds
    
    -- Output Configuration
    output_format VARCHAR(50) NOT NULL DEFAULT 'json', -- 'json', 'csv', 'database', 'api', 'file'
    output_destination JSONB NOT NULL DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',
    output_transformation JSONB DEFAULT '{}',
    
    -- LangGraph Orchestration
    trigger_type VARCHAR(50) NOT NULL DEFAULT 'manual', -- 'manual', 'scheduled', 'event', 'api', 'webhook'
    trigger_config JSONB DEFAULT '{}',
    schedule_cron VARCHAR(100), -- Cron expression for scheduled triggers
    event_listeners JSONB DEFAULT '[]', -- Event types to listen for
    
    -- HITL Configuration  
    hitl_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    hitl_trigger_conditions JSONB DEFAULT '{}',
    hitl_approval_required BOOLEAN DEFAULT FALSE,
    hitl_timeout_minutes INTEGER DEFAULT 60,
    hitl_escalation_rules JSONB DEFAULT '{}',
    
    -- Workflow Control
    max_execution_time_seconds INTEGER DEFAULT 3600,
    retry_policy JSONB DEFAULT '{"max_retries": 3, "backoff_multiplier": 2}',
    error_handling_strategy VARCHAR(50) DEFAULT 'fail', -- 'fail', 'continue', 'skip'
    
    -- Conditional Logic
    conditional_branches JSONB DEFAULT '[]',
    loop_configuration JSONB DEFAULT '{}',
    parallel_execution_enabled BOOLEAN DEFAULT FALSE,
    
    -- Monitoring & Logging
    logging_level VARCHAR(20) DEFAULT 'INFO',
    metrics_enabled BOOLEAN DEFAULT TRUE,
    alert_rules JSONB DEFAULT '[]',
    
    -- Version Control
    version INTEGER NOT NULL DEFAULT 1,
    change_log TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(agent_id, version)
);

CREATE INDEX idx_agent_builder_agent ON agent_builder_configs(agent_id);
CREATE INDEX idx_agent_builder_llm ON agent_builder_configs(llm_provider, llm_model);
CREATE INDEX idx_agent_builder_trigger ON agent_builder_configs(trigger_type);

-- ============================================================================
-- 3. DATABASE CONNECTIONS (For agents to connect to external DBs)
-- ============================================================================

CREATE TABLE IF NOT EXISTS database_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Connection details
    db_type VARCHAR(50) NOT NULL, -- 'postgresql', 'mysql', 'mongodb', 'sqlite', 'mssql'
    host VARCHAR(255),
    port INTEGER,
    database_name VARCHAR(255),
    username VARCHAR(255),
    password_encrypted TEXT, -- Encrypted password
    connection_string_template TEXT,
    
    -- Connection pooling
    pool_size INTEGER DEFAULT 5,
    max_overflow INTEGER DEFAULT 10,
    pool_timeout INTEGER DEFAULT 30,
    
    -- Security
    ssl_enabled BOOLEAN DEFAULT TRUE,
    ssl_cert TEXT,
    
    -- Access control
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    allowed_operations JSONB DEFAULT '["read"]', -- 'read', 'write', 'delete'
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_tested TIMESTAMP WITH TIME ZONE,
    last_test_status VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_db_type CHECK (db_type IN ('postgresql', 'mysql', 'mongodb', 'sqlite', 'mssql', 'oracle', 'redis'))
);

CREATE INDEX idx_db_connections_type ON database_connections(db_type);
CREATE INDEX idx_db_connections_active ON database_connections(is_active);

-- ============================================================================
-- 4. API CONFIGURATIONS (External API integrations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_configurations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- API details
    base_url TEXT NOT NULL,
    api_version VARCHAR(50),
    auth_type VARCHAR(50) NOT NULL, -- 'api_key', 'oauth2', 'basic', 'bearer', 'none'
    
    -- Authentication
    auth_credentials JSONB NOT NULL DEFAULT '{}', -- Encrypted credentials
    oauth_config JSONB,
    
    -- Rate limiting
    rate_limit_per_minute INTEGER,
    rate_limit_per_hour INTEGER,
    
    -- Headers & Configuration
    default_headers JSONB DEFAULT '{}',
    timeout_seconds INTEGER DEFAULT 30,
    retry_config JSONB DEFAULT '{"max_retries": 3, "backoff": "exponential"}',
    
    -- Documentation
    documentation_url TEXT,
    example_requests JSONB DEFAULT '[]',
    
    -- Access control
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_configs_name ON api_configurations(name);
CREATE INDEX idx_api_configs_active ON api_configurations(is_active);

-- ============================================================================
-- 5. TOOL REGISTRY (Enhanced tool management)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_registry (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    
    -- Tool type & category
    tool_type VARCHAR(50) NOT NULL, -- 'api', 'database', 'file', 'computation', 'llm', 'custom'
    category VARCHAR(100) NOT NULL,
    
    -- Implementation
    implementation_type VARCHAR(50) NOT NULL, -- 'python', 'api', 'sql', 'shell'
    code_reference TEXT, -- Python module path or code
    
    -- Parameters
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    parameter_hints JSONB DEFAULT '{}', -- UI hints for parameters
    
    -- Configuration
    requires_auth BOOLEAN DEFAULT FALSE,
    required_permissions JSONB DEFAULT '[]',
    cost_per_call DECIMAL(10,4) DEFAULT 0,
    
    -- Performance
    avg_execution_time_ms INTEGER,
    timeout_seconds INTEGER DEFAULT 30,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_premium BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Metadata
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    author VARCHAR(255),
    documentation_url TEXT,
    example_usage JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_tool_type CHECK (tool_type IN ('api', 'database', 'file', 'computation', 'llm', 'custom', 'integration'))
);

CREATE INDEX idx_tools_type ON tool_registry(tool_type);
CREATE INDEX idx_tools_category ON tool_registry(category);
CREATE INDEX idx_tools_active ON tool_registry(is_active);

-- ============================================================================
-- 6. AGENT EXECUTION TRIGGERS (Event-driven execution)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_execution_triggers (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    
    -- Trigger configuration
    trigger_name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    
    -- Trigger conditions
    conditions JSONB NOT NULL DEFAULT '{}',
    filters JSONB DEFAULT '{}',
    
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
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_trigger_type CHECK (trigger_type IN ('scheduled', 'webhook', 'event', 'manual', 'file_upload', 'database_change', 'api_call'))
);

CREATE INDEX idx_triggers_agent ON agent_execution_triggers(agent_id);
CREATE INDEX idx_triggers_type ON agent_execution_triggers(trigger_type);
CREATE INDEX idx_triggers_enabled ON agent_execution_triggers(is_enabled);

-- ============================================================================
-- 7. AGENT VARIABLES (Runtime variables and secrets)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_variables (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    
    -- Variable details
    variable_name VARCHAR(255) NOT NULL,
    variable_type VARCHAR(50) NOT NULL, -- 'string', 'number', 'boolean', 'secret', 'json'
    variable_value TEXT,
    encrypted_value TEXT, -- For secrets
    
    -- Metadata
    description TEXT,
    is_secret BOOLEAN NOT NULL DEFAULT FALSE,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    default_value TEXT,
    
    -- Scope
    scope VARCHAR(50) NOT NULL DEFAULT 'agent', -- 'agent', 'global', 'execution'
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(agent_id, variable_name),
    CONSTRAINT valid_variable_type CHECK (variable_type IN ('string', 'number', 'boolean', 'secret', 'json', 'array'))
);

CREATE INDEX idx_variables_agent ON agent_variables(agent_id);
CREATE INDEX idx_variables_scope ON agent_variables(scope);

-- ============================================================================
-- 8. AGENT VERSIONS (Version control for agents)
-- ============================================================================

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
    changed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Status
    is_deployed BOOLEAN NOT NULL DEFAULT FALSE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(agent_id, version_number)
);

CREATE INDEX idx_versions_agent ON agent_versions(agent_id);
CREATE INDEX idx_versions_deployed ON agent_versions(is_deployed);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agent_templates_updated_at BEFORE UPDATE ON agent_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_builder_configs_updated_at BEFORE UPDATE ON agent_builder_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_database_connections_updated_at BEFORE UPDATE ON database_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_configurations_updated_at BEFORE UPDATE ON api_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tool_registry_updated_at BEFORE UPDATE ON tool_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_execution_triggers_updated_at BEFORE UPDATE ON agent_execution_triggers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_variables_updated_at BEFORE UPDATE ON agent_variables
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================================

-- Insert sample tool registry entries
INSERT INTO tool_registry (name, display_name, description, tool_type, category, implementation_type, input_schema, output_schema) VALUES
('web_search', 'Web Search', 'Search the web using Google/Bing', 'api', 'search', 'api', '{"query": "string", "max_results": "integer"}', '{"results": "array"}'),
('database_query', 'Database Query', 'Execute SQL queries', 'database', 'data', 'sql', '{"query": "string", "parameters": "object"}', '{"rows": "array", "count": "integer"}'),
('csv_parser', 'CSV Parser', 'Parse and analyze CSV files', 'file', 'data', 'python', '{"file_path": "string", "delimiter": "string"}', '{"data": "array", "columns": "array"}'),
('json_transformer', 'JSON Transformer', 'Transform JSON data', 'computation', 'data', 'python', '{"input": "object", "transformation": "string"}', '{"output": "object"}'),
('llm_call', 'LLM Call', 'Make a call to an LLM', 'llm', 'ai', 'api', '{"prompt": "string", "model": "string"}', '{"response": "string", "tokens": "integer"}')
ON CONFLICT (name) DO NOTHING;

-- Insert sample agent template
INSERT INTO agent_templates (name, description, category, workflow_type, template_config) VALUES
('Data Processing Pipeline', 'Process and transform data from multiple sources', 'data_processing', 'data_pipeline', 
 '{"steps": ["extract", "transform", "load"], "supports_scheduling": true}')
ON CONFLICT (name) DO NOTHING;

COMMENT ON TABLE agent_templates IS 'Reusable agent configuration templates';
COMMENT ON TABLE agent_builder_configs IS 'Extended configuration for agent builder UI';
COMMENT ON TABLE database_connections IS 'External database connection configurations';
COMMENT ON TABLE api_configurations IS 'External API integration configurations';
COMMENT ON TABLE tool_registry IS 'Registry of available tools for agents';
COMMENT ON TABLE agent_execution_triggers IS 'Event-driven triggers for agent execution';
COMMENT ON TABLE agent_variables IS 'Runtime variables and secrets for agents';
COMMENT ON TABLE agent_versions IS 'Version control for agent configurations';
