"""
Agent Builder Service
Business logic for creating and managing agents

File: backend/app/services/agent_builder_service.py
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import json

from app.models.agent import AgentConfig
from app.schemas.agent_builder import (
    CompleteAgentCreate,
    AgentBuilderConfigCreate,
    AgentBuilderConfigUpdate,
    AgentVariableCreate,
    ExecutionTriggerCreate,
    LLMProvider,
    TriggerType,
    OutputFormat
)

logger = logging.getLogger(__name__)


class AgentBuilderService:
    """
    Service for creating and managing agents with comprehensive configuration
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========================================================================
    # AGENT CREATION
    # ========================================================================
    
    def create_complete_agent(
        self,
        agent_data: CompleteAgentCreate,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Create a complete agent with all configurations
        
        This is the main entry point for creating agents via UI
        """
        try:
            # 1. Create base agent
            agent = AgentConfig(
                name=agent_data.name,
                description=agent_data.description,
                workflow=agent_data.workflow,
                config={},  # Will be populated from builder_config
                active=True,
                created_by=7
            )
            
            self.db.add(agent)
            self.db.flush()  # Get agent ID
            
            logger.info(f"Created base agent: {agent.id} - {agent.name}")
            
            # 2. Create builder configuration
            builder_config_id = self._create_builder_config(
                agent.id,
                agent_data.builder_config
            )
            
            # 3. Update agent config with builder settings
            agent.config = self._generate_agent_config(agent_data.builder_config)
            
            # 4. Create variables
            if agent_data.variables:
                self._create_variables(agent.id, agent_data.variables)
            
            # 5. Create triggers
            if agent_data.triggers:
                self._create_triggers(agent.id, agent_data.triggers)
            
            self.db.commit()
            
            logger.info(f"Successfully created complete agent: {agent.id}")
            
            return {
                "id": agent.id,
                "name": agent.name,
                "builder_config_id": builder_config_id,
                "status": "created"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    def _create_builder_config(
        self,
        agent_id: int,
        config: AgentBuilderConfigCreate
    ) -> int:
        """Create agent builder configuration"""
        
        # Convert Pydantic models to dict for JSONB storage
        enabled_tools_json = [tool.dict() for tool in config.enabled_tools]
        
        query = text("""
            INSERT INTO agent_builder_configs (
                agent_id,
                llm_provider, llm_model, llm_temperature, llm_max_tokens,
                llm_api_endpoint, llm_api_key_ref,
                input_schema, input_preprocessing, input_validation_rules,
                enabled_tools, tool_timeout_seconds, max_tool_calls,
                db_connection_id, db_queries, db_write_enabled,
                api_endpoints, api_auth_method, api_rate_limit,
                data_sources, data_refresh_interval,
                output_format, output_destination, output_schema, output_transformation,
                trigger_type, trigger_config, schedule_cron, event_listeners,
                hitl_enabled, hitl_trigger_conditions, hitl_approval_required,
                hitl_timeout_minutes, hitl_escalation_rules,
                max_execution_time_seconds, retry_policy, error_handling_strategy,
                conditional_branches, loop_configuration, parallel_execution_enabled,
                logging_level, metrics_enabled, alert_rules,
                version
            ) VALUES (
                :agent_id,
                :llm_provider, :llm_model, :llm_temperature, :llm_max_tokens,
                :llm_api_endpoint, :llm_api_key_ref,
                :input_schema, :input_preprocessing, :input_validation_rules,
                :enabled_tools, :tool_timeout_seconds, :max_tool_calls,
                :db_connection_id, :db_queries, :db_write_enabled,
                :api_endpoints, :api_auth_method, :api_rate_limit,
                :data_sources, :data_refresh_interval,
                :output_format, :output_destination, :output_schema, :output_transformation,
                :trigger_type, :trigger_config, :schedule_cron, :event_listeners,
                :hitl_enabled, :hitl_trigger_conditions, :hitl_approval_required,
                :hitl_timeout_minutes, :hitl_escalation_rules,
                :max_execution_time_seconds, :retry_policy, :error_handling_strategy,
                :conditional_branches, :loop_configuration, :parallel_execution_enabled,
                :logging_level, :metrics_enabled, :alert_rules,
                :version
            ) RETURNING id
        """)
        
        result = self.db.execute(query, {
            "agent_id": agent_id,
            "llm_provider": config.llm_config.provider.value,
            "llm_model": config.llm_config.model,
            "llm_temperature": float(config.llm_config.temperature),
            "llm_max_tokens": config.llm_config.max_tokens,
            "llm_api_endpoint": config.llm_config.api_endpoint,
            "llm_api_key_ref": config.llm_config.api_key_ref,
            "input_schema": json.dumps(config.input_config.schema_definition),
            "input_preprocessing": json.dumps(config.input_config.preprocessing_steps),
            "input_validation_rules": json.dumps(config.input_config.validation_rules),
            "enabled_tools": json.dumps(enabled_tools_json),
            "tool_timeout_seconds": config.tool_timeout_seconds,
            "max_tool_calls": config.max_tool_calls,
            "db_connection_id": config.db_connection_id,
            "db_queries": json.dumps(config.db_queries),
            "db_write_enabled": config.db_write_enabled,
            "api_endpoints": json.dumps(config.api_endpoints),
            "api_auth_method": config.api_auth_method,
            "api_rate_limit": config.api_rate_limit,
            "data_sources": json.dumps(config.data_sources),
            "data_refresh_interval": config.data_refresh_interval,
            "output_format": config.output_config.format.value,
            "output_destination": json.dumps(config.output_config.destination),
            "output_schema": json.dumps(config.output_config.schema_definition),
            "output_transformation": json.dumps(config.output_config.transformation),
            "trigger_type": config.trigger_config.trigger_type.value,
            "trigger_config": json.dumps(config.trigger_config.config),
            "schedule_cron": config.trigger_config.schedule_cron,
            "event_listeners": json.dumps(config.trigger_config.event_listeners),
            "hitl_enabled": config.hitl_config.enabled,
            "hitl_trigger_conditions": json.dumps(config.hitl_config.trigger_conditions),
            "hitl_approval_required": config.hitl_config.approval_required,
            "hitl_timeout_minutes": config.hitl_config.timeout_minutes,
            "hitl_escalation_rules": json.dumps(config.hitl_config.escalation_rules),
            "max_execution_time_seconds": config.workflow_control.max_execution_time_seconds,
            "retry_policy": json.dumps(config.workflow_control.retry_policy),
            "error_handling_strategy": config.workflow_control.error_handling_strategy.value,
            "conditional_branches": json.dumps(config.workflow_control.conditional_branches),
            "loop_configuration": json.dumps(config.workflow_control.loop_configuration),
            "parallel_execution_enabled": config.workflow_control.parallel_execution_enabled,
            "logging_level": config.logging_level,
            "metrics_enabled": config.metrics_enabled,
            "alert_rules": json.dumps(config.alert_rules),
            "version": 1
        })
        
        return result.fetchone()[0]
    
    def _generate_agent_config(self, builder_config: AgentBuilderConfigCreate) -> Dict[str, Any]:
        """
        Generate agent config from builder configuration
        
        This creates the config dict that's compatible with existing agent execution
        """
        return {
            "llm": {
                "provider": builder_config.llm_config.provider.value,
                "model": builder_config.llm_config.model,
                "temperature": builder_config.llm_config.temperature,
                "max_tokens": builder_config.llm_config.max_tokens
            },
            "tools": {
                "enabled": len(builder_config.enabled_tools) > 0,
                "allowed_tools": [tool.tool_name for tool in builder_config.enabled_tools],
                "timeout": builder_config.tool_timeout_seconds
            },
            "hitl": {
                "enabled": builder_config.hitl_config.enabled,
                "approval_required": builder_config.hitl_config.approval_required,
                "timeout_minutes": builder_config.hitl_config.timeout_minutes
            },
            "output": {
                "format": builder_config.output_config.format.value,
                "destination": builder_config.output_config.destination
            },
            "trigger": {
                "type": builder_config.trigger_config.trigger_type.value,
                "config": builder_config.trigger_config.config
            },
            "workflow_control": {
                "max_execution_time": builder_config.workflow_control.max_execution_time_seconds,
                "retry_policy": builder_config.workflow_control.retry_policy,
                "error_strategy": builder_config.workflow_control.error_handling_strategy.value
            }
        }
    
    def _create_variables(self, agent_id: int, variables: List[AgentVariableCreate]):
        """Create agent variables"""
        for var in variables:
            # Handle secret encryption if needed
            encrypted_value = None
            plain_value = var.variable_value
            
            if var.is_secret and var.variable_value:
                # TODO: Implement proper encryption
                encrypted_value = self._encrypt_secret(var.variable_value)
                plain_value = None
            
            query = text("""
                INSERT INTO agent_variables (
                    agent_id, variable_name, variable_type, variable_value,
                    encrypted_value, description, is_secret, is_required,
                    default_value, scope
                ) VALUES (
                    :agent_id, :variable_name, :variable_type, :variable_value,
                    :encrypted_value, :description, :is_secret, :is_required,
                    :default_value, :scope
                )
            """)
            
            self.db.execute(query, {
                "agent_id": agent_id,
                "variable_name": var.variable_name,
                "variable_type": var.variable_type,
                "variable_value": plain_value,
                "encrypted_value": encrypted_value,
                "description": var.description,
                "is_secret": var.is_secret,
                "is_required": var.is_required,
                "default_value": var.default_value,
                "scope": var.scope
            })
    
    def _create_triggers(self, agent_id: int, triggers: List[ExecutionTriggerCreate]):
        """Create execution triggers"""
        for trigger in triggers:
            query = text("""
                INSERT INTO agent_execution_triggers (
                    agent_id, trigger_name, trigger_type, conditions, filters,
                    webhook_url, webhook_secret, cron_expression, timezone, is_enabled
                ) VALUES (
                    :agent_id, :trigger_name, :trigger_type, :conditions, :filters,
                    :webhook_url, :webhook_secret, :cron_expression, :timezone, :is_enabled
                )
            """)
            
            self.db.execute(query, {
                "agent_id": agent_id,
                "trigger_name": trigger.trigger_name,
                "trigger_type": trigger.trigger_type.value,
                "conditions": json.dumps(trigger.conditions),
                "filters": json.dumps(trigger.filters),
                "webhook_url": trigger.webhook_url,
                "webhook_secret": trigger.webhook_secret,
                "cron_expression": trigger.cron_expression,
                "timezone": trigger.timezone,
                "is_enabled": True
            })
    
    def _encrypt_secret(self, value: str) -> str:
        """
        Encrypt secret value
        
        TODO: Implement proper encryption using cryptography library
        """
        # Placeholder - implement proper encryption
        from base64 import b64encode
        return b64encode(value.encode()).decode()
    
    def _decrypt_secret(self, encrypted: str) -> str:
        """Decrypt secret value"""
        from base64 import b64decode
        return b64decode(encrypted.encode()).decode()
    
    # ========================================================================
    # AGENT RETRIEVAL
    # ========================================================================
    
    def get_agent_with_config(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Get agent with full builder configuration"""
        
        # Get base agent
        agent = self.db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
        if not agent:
            return None
        
        # Get builder config
        query = text("""
            SELECT * FROM agent_builder_configs
            WHERE agent_id = :agent_id
            ORDER BY version DESC
            LIMIT 1
        """)
        
        result = self.db.execute(query, {"agent_id": agent_id})
        builder_config = result.fetchone()
        
        # Get variables
        var_query = text("""
            SELECT * FROM agent_variables
            WHERE agent_id = :agent_id
        """)
        variables = self.db.execute(var_query, {"agent_id": agent_id}).fetchall()
        
        # Get triggers
        trigger_query = text("""
            SELECT * FROM agent_execution_triggers
            WHERE agent_id = :agent_id
        """)
        triggers = self.db.execute(trigger_query, {"agent_id": agent_id}).fetchall()
        
        return {
            "agent": agent.to_dict(),
            "builder_config": dict(builder_config) if builder_config else None,
            "variables": [dict(v) for v in variables],
            "triggers": [dict(t) for t in triggers]
        }
    
    def list_agents_with_summary(
        self,
        workflow: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """List agents with summary information"""
        
        query_str = """
            SELECT 
                a.*,
                abc.llm_provider,
                abc.llm_model,
                abc.trigger_type,
                abc.hitl_enabled,
                (SELECT COUNT(*) FROM agent_variables WHERE agent_id = a.id) as var_count,
                (SELECT COUNT(*) FROM agent_execution_triggers WHERE agent_id = a.id) as trigger_count
            FROM agents a
            LEFT JOIN agent_builder_configs abc ON a.id = abc.agent_id
            WHERE 1=1
        """
        
        params = {}
        if workflow:
            query_str += " AND a.workflow = :workflow"
            params["workflow"] = workflow
        
        if active_only:
            query_str += " AND a.active = true"
        
        query_str += " ORDER BY a.created_at DESC"
        
        result = self.db.execute(text(query_str), params)
        
        return [dict(row) for row in result.fetchall()]
    
    # ========================================================================
    # AGENT UPDATE
    # ========================================================================
    
    def update_builder_config(
        self,
        agent_id: int,
        updates: AgentBuilderConfigUpdate
    ) -> bool:
        """Update agent builder configuration"""
        
        try:
            # Get current config
            query = text("""
                SELECT id, version FROM agent_builder_configs
                WHERE agent_id = :agent_id
                ORDER BY version DESC
                LIMIT 1
            """)
            result = self.db.execute(query, {"agent_id": agent_id})
            current = result.fetchone()
            
            if not current:
                logger.error(f"No builder config found for agent {agent_id}")
                return False
            
            # Build update query dynamically
            update_fields = []
            params = {"config_id": current[0]}
            
            if updates.llm_config:
                update_fields.extend([
                    "llm_provider = :llm_provider",
                    "llm_model = :llm_model",
                    "llm_temperature = :llm_temperature",
                    "llm_max_tokens = :llm_max_tokens"
                ])
                params.update({
                    "llm_provider": updates.llm_config.provider.value,
                    "llm_model": updates.llm_config.model,
                    "llm_temperature": float(updates.llm_config.temperature),
                    "llm_max_tokens": updates.llm_config.max_tokens
                })
            
            if updates.enabled_tools is not None:
                update_fields.append("enabled_tools = :enabled_tools")
                params["enabled_tools"] = json.dumps([t.dict() for t in updates.enabled_tools])
            
            if updates.output_config:
                update_fields.extend([
                    "output_format = :output_format",
                    "output_destination = :output_destination"
                ])
                params.update({
                    "output_format": updates.output_config.format.value,
                    "output_destination": json.dumps(updates.output_config.destination)
                })
            
            if updates.trigger_config:
                update_fields.extend([
                    "trigger_type = :trigger_type",
                    "trigger_config = :trigger_config"
                ])
                params.update({
                    "trigger_type": updates.trigger_config.trigger_type.value,
                    "trigger_config": json.dumps(updates.trigger_config.config)
                })
            
            if updates.hitl_config:
                update_fields.extend([
                    "hitl_enabled = :hitl_enabled",
                    "hitl_approval_required = :hitl_approval_required"
                ])
                params.update({
                    "hitl_enabled": updates.hitl_config.enabled,
                    "hitl_approval_required": updates.hitl_config.approval_required
                })
            
            if not update_fields:
                logger.info("No fields to update")
                return True
            
            update_query = text(f"""
                UPDATE agent_builder_configs
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = :config_id
            """)
            
            self.db.execute(update_query, params)
            self.db.commit()
            
            logger.info(f"Updated builder config for agent {agent_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating builder config: {str(e)}")
            raise
    
    # ========================================================================
    # DROPDOWN OPTIONS
    # ========================================================================
    
    def get_dropdown_options(self) -> Dict[str, Any]:
        """Get all dropdown options for UI"""
        
        return {
            "llm_providers": [
                {"value": "openai", "label": "OpenAI"},
                {"value": "anthropic", "label": "Anthropic (Claude)"},
                {"value": "ollama", "label": "Ollama (Local)"},
                {"value": "azure", "label": "Azure OpenAI"},
                {"value": "cohere", "label": "Cohere"},
                {"value": "huggingface", "label": "Hugging Face"}
            ],
            "llm_models": {
                "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "ollama": ["llama2", "mistral", "codellama", "phi"],
                "azure": ["gpt-4", "gpt-35-turbo"],
                "cohere": ["command", "command-light"],
                "huggingface": ["custom"]
            },
            "trigger_types": [
                {"value": "manual", "label": "Manual Trigger"},
                {"value": "scheduled", "label": "Scheduled (Cron)"},
                {"value": "event", "label": "Event-Driven"},
                {"value": "api", "label": "API Call"},
                {"value": "webhook", "label": "Webhook"},
                {"value": "file_upload", "label": "File Upload"},
                {"value": "database_change", "label": "Database Change"}
            ],
            "output_formats": [
                {"value": "json", "label": "JSON"},
                {"value": "csv", "label": "CSV"},
                {"value": "database", "label": "Database"},
                {"value": "api", "label": "API Call"},
                {"value": "file", "label": "File"},
                {"value": "spreadsheet", "label": "Spreadsheet"}
            ],
            "workflow_types": [
                {"value": "simple", "label": "Simple Workflow"},
                {"value": "data_pipeline", "label": "Data Pipeline"},
                {"value": "api_orchestration", "label": "API Orchestration"},
                {"value": "ml_inference", "label": "ML Inference"},
                {"value": "research", "label": "Research Workflow"},
                {"value": "custom", "label": "Custom Workflow"}
            ],
            "error_strategies": [
                {"value": "fail", "label": "Fail Immediately"},
                {"value": "continue", "label": "Continue on Error"},
                {"value": "skip", "label": "Skip Failed Step"},
                {"value": "retry", "label": "Retry with Backoff"}
            ],
            "logging_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "tool_categories": [
                {"value": "api", "label": "API Integration"},
                {"value": "database", "label": "Database"},
                {"value": "file", "label": "File Processing"},
                {"value": "computation", "label": "Computation"},
                {"value": "llm", "label": "LLM Tools"},
                {"value": "integration", "label": "Integration"}
            ]
        }
    
    def get_available_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available tools for selection"""
        
        query_str = """
            SELECT id, name, display_name, description, tool_type, category,
                   input_schema, is_premium, requires_auth
            FROM tool_registry
            WHERE is_active = true
        """
        
        params = {}
        if category:
            query_str += " AND category = :category"
            params["category"] = category
        
        query_str += " ORDER BY category, display_name"
        
        result = self.db.execute(text(query_str), params)
        
        return [dict(row) for row in result.fetchall()]
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate_agent_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate agent configuration
        
        Returns validation result with errors, warnings, and suggestions
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Validate LLM config
        if "llm_config" in config:
            llm = config["llm_config"]
            if not llm.get("model"):
                errors.append({"field": "llm_config.model", "message": "LLM model is required"})
            if llm.get("temperature", 0) > 1.5:
                warnings.append({"field": "llm_config.temperature", "message": "High temperature may produce inconsistent results"})
        
        # Validate tools
        if "enabled_tools" in config and len(config["enabled_tools"]) == 0:
            warnings.append({"field": "enabled_tools", "message": "No tools enabled - agent may have limited capabilities"})
        
        # Validate output
        if "output_config" in config:
            output = config["output_config"]
            if output.get("format") == "database" and not output.get("destination"):
                errors.append({"field": "output_config.destination", "message": "Database destination required for database output"})
        
        # Suggestions
        if config.get("hitl_config", {}).get("enabled") and not config.get("trigger_config", {}).get("trigger_type") == "manual":
            suggestions.append("Consider using manual trigger when HITL is enabled")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
