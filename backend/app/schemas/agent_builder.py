"""
Agent Builder Schemas
Pydantic models for the Agent Builder API

File: backend/app/schemas/agent_builder.py
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


# ============================================================================
# ENUMS
# ============================================================================

class LLMProvider(str, Enum):
    """LLM provider options"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    AZURE = "azure"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class TriggerType(str, Enum):
    """Agent trigger types"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    API = "api"
    WEBHOOK = "webhook"
    FILE_UPLOAD = "file_upload"
    DATABASE_CHANGE = "database_change"


class OutputFormat(str, Enum):
    """Output format options"""
    JSON = "json"
    CSV = "csv"
    DATABASE = "database"
    API = "api"
    FILE = "file"
    SPREADSHEET = "spreadsheet"


class ToolType(str, Enum):
    """Tool types"""
    API = "api"
    DATABASE = "database"
    FILE = "file"
    COMPUTATION = "computation"
    LLM = "llm"
    CUSTOM = "custom"
    INTEGRATION = "integration"


class ErrorHandlingStrategy(str, Enum):
    """Error handling strategies"""
    FAIL = "fail"
    CONTINUE = "continue"
    SKIP = "skip"
    RETRY = "retry"


# ============================================================================
# DATABASE CONNECTION SCHEMAS
# ============================================================================

class DatabaseConnectionCreate(BaseModel):
    """Create database connection"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    db_type: str = Field(..., description="Database type: postgresql, mysql, mongodb, etc.")
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, description="Will be encrypted")
    connection_string_template: Optional[str] = None
    pool_size: int = Field(5, ge=1, le=100)
    max_overflow: int = Field(10, ge=0, le=50)
    ssl_enabled: bool = True
    allowed_operations: List[str] = Field(default_factory=lambda: ["read"])


class DatabaseConnectionResponse(BaseModel):
    """Database connection response"""
    id: int
    name: str
    description: Optional[str]
    db_type: str
    host: Optional[str]
    port: Optional[int]
    database_name: Optional[str]
    is_active: bool
    last_tested: Optional[datetime]
    last_test_status: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# API CONFIGURATION SCHEMAS
# ============================================================================

class APIConfigurationCreate(BaseModel):
    """Create API configuration"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    base_url: str
    api_version: Optional[str] = None
    auth_type: str = Field(..., description="api_key, oauth2, basic, bearer, none")
    auth_credentials: Dict[str, Any] = Field(default_factory=dict)
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_hour: Optional[int] = None
    default_headers: Dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = Field(30, ge=1, le=300)
    documentation_url: Optional[str] = None


class APIConfigurationResponse(BaseModel):
    """API configuration response"""
    id: int
    name: str
    description: Optional[str]
    base_url: str
    auth_type: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# TOOL REGISTRY SCHEMAS
# ============================================================================

class ToolCreate(BaseModel):
    """Create tool"""
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str
    description: str
    tool_type: ToolType
    category: str
    implementation_type: str = Field(..., description="python, api, sql, shell")
    code_reference: Optional[str] = None
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    parameter_hints: Dict[str, Any] = Field(default_factory=dict)
    requires_auth: bool = False
    timeout_seconds: int = Field(30, ge=1, le=600)
    documentation_url: Optional[str] = None


class ToolResponse(BaseModel):
    """Tool response"""
    id: int
    name: str
    display_name: str
    description: str
    tool_type: str
    category: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    is_active: bool
    is_premium: bool
    version: str
    
    class Config:
        from_attributes = True


# ============================================================================
# AGENT BUILDER CONFIG SCHEMAS
# ============================================================================

class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = Field("gpt-4", description="Model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2000, ge=1, le=100000)
    api_endpoint: Optional[str] = None
    api_key_ref: Optional[str] = Field(None, description="Reference to secure key storage")


class InputConfig(BaseModel):
    """Input configuration"""
    schema_definition: Dict[str, Any] = Field(default_factory=dict)
    preprocessing_steps: List[Dict[str, Any]] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)


class ToolConfig(BaseModel):
    """Tool configuration for an agent"""
    tool_id: int
    tool_name: str
    enabled: bool = True
    configuration: Dict[str, Any] = Field(default_factory=dict)
    timeout_override: Optional[int] = None


class OutputConfig(BaseModel):
    """Output configuration"""
    format: OutputFormat = OutputFormat.JSON
    destination: Dict[str, Any] = Field(default_factory=dict)
    schema_definition: Dict[str, Any] = Field(default_factory=dict)
    transformation: Dict[str, Any] = Field(default_factory=dict)


class TriggerConfig(BaseModel):
    """Trigger configuration"""
    trigger_type: TriggerType = TriggerType.MANUAL
    config: Dict[str, Any] = Field(default_factory=dict)
    schedule_cron: Optional[str] = None
    event_listeners: List[str] = Field(default_factory=list)


class HITLConfig(BaseModel):
    """HITL configuration"""
    enabled: bool = False
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict)
    approval_required: bool = False
    timeout_minutes: int = Field(60, ge=1, le=1440)
    escalation_rules: Dict[str, Any] = Field(default_factory=dict)


class WorkflowControlConfig(BaseModel):
    """Workflow control configuration"""
    max_execution_time_seconds: int = Field(3600, ge=1, le=86400)
    retry_policy: Dict[str, Any] = Field(
        default_factory=lambda: {"max_retries": 3, "backoff_multiplier": 2}
    )
    error_handling_strategy: ErrorHandlingStrategy = ErrorHandlingStrategy.FAIL
    conditional_branches: List[Dict[str, Any]] = Field(default_factory=list)
    loop_configuration: Dict[str, Any] = Field(default_factory=dict)
    parallel_execution_enabled: bool = False


class AgentBuilderConfigCreate(BaseModel):
    """Create agent builder configuration"""
    agent_id: int
    
    # LLM Configuration
    llm_config: LLMConfig
    
    # Input Configuration
    input_config: InputConfig
    
    # Tool Configuration
    enabled_tools: List[ToolConfig] = Field(default_factory=list)
    tool_timeout_seconds: int = Field(300, ge=1, le=3600)
    max_tool_calls: int = Field(10, ge=1, le=100)
    
    # Database Integration
    db_connection_id: Optional[int] = None
    db_queries: List[Dict[str, Any]] = Field(default_factory=list)
    db_write_enabled: bool = False
    
    # API Integration
    api_endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    api_auth_method: Optional[str] = None
    api_rate_limit: Optional[int] = None
    
    # Data Sources
    data_sources: List[Dict[str, Any]] = Field(default_factory=list)
    data_refresh_interval: Optional[int] = None
    
    # Output Configuration
    output_config: OutputConfig
    
    # Trigger Configuration
    trigger_config: TriggerConfig
    
    # HITL Configuration
    hitl_config: HITLConfig
    
    # Workflow Control
    workflow_control: WorkflowControlConfig
    
    # Monitoring
    logging_level: str = Field("INFO", description="DEBUG, INFO, WARNING, ERROR")
    metrics_enabled: bool = True
    alert_rules: List[Dict[str, Any]] = Field(default_factory=list)


class AgentBuilderConfigUpdate(BaseModel):
    """Update agent builder configuration"""
    llm_config: Optional[LLMConfig] = None
    input_config: Optional[InputConfig] = None
    enabled_tools: Optional[List[ToolConfig]] = None
    output_config: Optional[OutputConfig] = None
    trigger_config: Optional[TriggerConfig] = None
    hitl_config: Optional[HITLConfig] = None
    workflow_control: Optional[WorkflowControlConfig] = None
    metrics_enabled: Optional[bool] = None


class AgentBuilderConfigResponse(BaseModel):
    """Agent builder configuration response"""
    id: int
    agent_id: int
    
    # LLM
    llm_provider: str
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int
    
    # Tools
    enabled_tools: List[Dict[str, Any]]
    
    # Integration
    db_connection_id: Optional[int]
    api_endpoints: List[Dict[str, Any]]
    data_sources: List[Dict[str, Any]]
    
    # Output
    output_format: str
    output_destination: Dict[str, Any]
    
    # Trigger
    trigger_type: str
    trigger_config: Dict[str, Any]
    
    # HITL
    hitl_enabled: bool
    hitl_approval_required: bool
    
    # Metadata
    version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# AGENT TEMPLATE SCHEMAS
# ============================================================================

class AgentTemplateCreate(BaseModel):
    """Create agent template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str
    icon: Optional[str] = None
    template_config: Dict[str, Any] = Field(default_factory=dict)
    default_tools: List[int] = Field(default_factory=list)
    required_fields: List[str] = Field(default_factory=list)
    workflow_type: str
    node_configuration: Dict[str, Any] = Field(default_factory=dict)


class AgentTemplateResponse(BaseModel):
    """Agent template response"""
    id: int
    name: str
    description: Optional[str]
    category: str
    icon: Optional[str]
    template_config: Dict[str, Any]
    default_tools: List[int]
    workflow_type: str
    is_official: bool
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# AGENT VARIABLE SCHEMAS
# ============================================================================

class AgentVariableCreate(BaseModel):
    """Create agent variable"""
    agent_id: int
    variable_name: str = Field(..., min_length=1, max_length=255)
    variable_type: str = Field(..., description="string, number, boolean, secret, json")
    variable_value: Optional[str] = None
    description: Optional[str] = None
    is_secret: bool = False
    is_required: bool = False
    default_value: Optional[str] = None
    scope: str = Field("agent", description="agent, global, execution")


class AgentVariableResponse(BaseModel):
    """Agent variable response"""
    id: int
    agent_id: Optional[int]
    variable_name: str
    variable_type: str
    variable_value: Optional[str]  # Secrets will be masked
    description: Optional[str]
    is_secret: bool
    is_required: bool
    scope: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# EXECUTION TRIGGER SCHEMAS
# ============================================================================

class ExecutionTriggerCreate(BaseModel):
    """Create execution trigger"""
    agent_id: int
    trigger_name: str
    trigger_type: TriggerType
    conditions: Dict[str, Any] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: str = "UTC"


class ExecutionTriggerResponse(BaseModel):
    """Execution trigger response"""
    id: int
    agent_id: int
    trigger_name: str
    trigger_type: str
    is_enabled: bool
    last_triggered: Optional[datetime]
    trigger_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# COMPREHENSIVE AGENT CREATION SCHEMAS
# ============================================================================

class CompleteAgentCreate(BaseModel):
    """Complete agent creation with all configurations"""
    # Basic agent info
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    workflow: str
    
    # Builder configuration
    builder_config: AgentBuilderConfigCreate
    
    # Optional: Use template
    template_id: Optional[int] = None
    
    # Optional: Variables
    variables: List[AgentVariableCreate] = Field(default_factory=list)
    
    # Optional: Triggers
    triggers: List[ExecutionTriggerCreate] = Field(default_factory=list)


class CompleteAgentResponse(BaseModel):
    """Complete agent with all configurations"""
    # Basic info
    id: int
    name: str
    description: Optional[str]
    workflow: str
    active: bool
    version: int
    
    # Builder config
    builder_config: Optional[AgentBuilderConfigResponse] = None
    
    # Variables count
    variables_count: int = 0
    
    # Triggers count
    triggers_count: int = 0
    
    # Metadata
    created_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]


# ============================================================================
# AGENT VERSION SCHEMAS
# ============================================================================

class AgentVersionResponse(BaseModel):
    """Agent version response"""
    id: int
    agent_id: int
    version_number: int
    version_tag: Optional[str]
    change_description: Optional[str]
    is_deployed: bool
    deployed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# UI DROPDOWN OPTIONS
# ============================================================================

class DropdownOptions(BaseModel):
    """Dropdown options for UI"""
    llm_providers: List[Dict[str, str]]
    llm_models: Dict[str, List[str]]  # Provider -> models
    trigger_types: List[Dict[str, str]]
    output_formats: List[Dict[str, str]]
    tool_categories: List[Dict[str, str]]
    workflow_types: List[Dict[str, str]]
    error_strategies: List[Dict[str, str]]
    logging_levels: List[str]


# ============================================================================
# VALIDATION & TESTING SCHEMAS
# ============================================================================

class ConfigValidationRequest(BaseModel):
    """Validate configuration"""
    agent_config: Dict[str, Any]
    builder_config: Dict[str, Any]


class ConfigValidationResponse(BaseModel):
    """Configuration validation result"""
    is_valid: bool
    errors: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[Dict[str, str]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class AgentTestRequest(BaseModel):
    """Test agent execution"""
    agent_id: int
    test_input: Dict[str, Any]
    dry_run: bool = True


class AgentTestResponse(BaseModel):
    """Agent test result"""
    success: bool
    execution_id: Optional[str]
    output: Optional[Dict[str, Any]]
    error: Optional[str]
    execution_time_ms: int
    steps_executed: List[str]
