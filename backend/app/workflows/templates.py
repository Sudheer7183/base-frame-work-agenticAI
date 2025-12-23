"""
Workflow Templates
Pre-built workflow configurations for common use cases
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Standard workflow types"""
    SIMPLE_CHAT = "simple_chat"
    APPROVAL = "approval"
    DATA_PROCESSING = "data_processing"
    MULTI_AGENT = "multi_agent"
    RESEARCH = "research"
    CUSTOMER_SUPPORT = "customer_support"
    CONTENT_GENERATION = "content_generation"


@dataclass
class WorkflowTemplate:
    """Workflow template definition"""
    name: str
    type: WorkflowType
    description: str
    config: Dict[str, Any]
    nodes: List[str]
    edges: List[tuple]
    required_tools: List[str] = None
    recommended_llm: str = "gpt-4"
    estimated_cost_per_run: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "config": self.config,
            "nodes": self.nodes,
            "edges": self.edges,
            "required_tools": self.required_tools or [],
            "recommended_llm": self.recommended_llm,
            "estimated_cost_per_run": self.estimated_cost_per_run
        }


class WorkflowTemplateRegistry:
    """
    Registry for workflow templates
    Manages pre-built workflow configurations
    """
    
    def __init__(self):
        self._templates: Dict[str, WorkflowTemplate] = {}
        self._register_default_templates()
        logger.info("Workflow template registry initialized")
    
    def _register_default_templates(self):
        """Register default workflow templates"""
        
        # 1. Simple Chat Workflow
        self.register(WorkflowTemplate(
            name="Simple Chat",
            type=WorkflowType.SIMPLE_CHAT,
            description="Basic conversational workflow without tools or HITL",
            config={
                "llm": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "hitl": {
                    "enabled": False
                }
            },
            nodes=["validate_input", "process_llm", "format_output"],
            edges=[
                ("validate_input", "process_llm"),
                ("process_llm", "format_output"),
                ("format_output", "END")
            ],
            estimated_cost_per_run=0.01
        ))
        
        # 2. Approval Workflow
        self.register(WorkflowTemplate(
            name="Approval Workflow",
            type=WorkflowType.APPROVAL,
            description="Workflow with mandatory human approval for sensitive operations",
            config={
                "llm": {
                    "model": "gpt-4",
                    "temperature": 0.3
                },
                "hitl": {
                    "enabled": True,
                    "threshold": 0.9,
                    "always_required": True,
                    "timeout_hours": 24
                }
            },
            nodes=["validate_input", "process_llm", "hitl_gate", "format_output"],
            edges=[
                ("validate_input", "process_llm"),
                ("process_llm", "hitl_gate"),
                ("hitl_gate", "format_output"),
                ("format_output", "END")
            ],
            estimated_cost_per_run=0.02
        ))
        
        # 3. Data Processing Workflow
        self.register(WorkflowTemplate(
            name="Data Processing",
            type=WorkflowType.DATA_PROCESSING,
            description="Extract, transform, and analyze data with tool support",
            config={
                "llm": {
                    "model": "gpt-4",
                    "temperature": 0.1
                },
                "tools": {
                    "enabled": True,
                    "allowed_tools": ["database_query", "calculator", "data_export"]
                },
                "hitl": {
                    "enabled": True,
                    "threshold": 0.7
                }
            },
            nodes=[
                "validate_input",
                "extract_data",
                "process_llm",
                "execute_tools",
                "hitl_gate",
                "format_output"
            ],
            edges=[
                ("validate_input", "extract_data"),
                ("extract_data", "process_llm"),
                ("process_llm", "execute_tools"),
                ("execute_tools", "hitl_gate"),
                ("hitl_gate", "format_output"),
                ("format_output", "END")
            ],
            required_tools=["database_query", "calculator"],
            estimated_cost_per_run=0.05
        ))
        
        # 4. Research Workflow
        self.register(WorkflowTemplate(
            name="Research Workflow",
            type=WorkflowType.RESEARCH,
            description="Multi-step research with web search and analysis",
            config={
                "llm": {
                    "model": "gpt-4",
                    "temperature": 0.4
                },
                "tools": {
                    "enabled": True,
                    "allowed_tools": ["search", "web_scrape", "summarize"]
                },
                "max_iterations": 5,
                "hitl": {
                    "enabled": True,
                    "threshold": 0.6
                }
            },
            nodes=[
                "validate_input",
                "plan_research",
                "search_web",
                "analyze_results",
                "synthesize",
                "hitl_gate",
                "format_output"
            ],
            edges=[
                ("validate_input", "plan_research"),
                ("plan_research", "search_web"),
                ("search_web", "analyze_results"),
                ("analyze_results", "synthesize"),
                ("synthesize", "hitl_gate"),
                ("hitl_gate", "format_output"),
                ("format_output", "END")
            ],
            required_tools=["search"],
            estimated_cost_per_run=0.15
        ))
        
        # 5. Customer Support Workflow
        self.register(WorkflowTemplate(
            name="Customer Support",
            type=WorkflowType.CUSTOMER_SUPPORT,
            description="Handle customer inquiries with knowledge base and escalation",
            config={
                "llm": {
                    "model": "gpt-4",
                    "temperature": 0.5
                },
                "tools": {
                    "enabled": True,
                    "allowed_tools": ["knowledge_base", "ticket_system"]
                },
                "hitl": {
                    "enabled": True,
                    "threshold": 0.8,
                    "escalation_keywords": ["complaint", "urgent", "manager"]
                }
            },
            nodes=[
                "validate_input",
                "classify_intent",
                "search_knowledge",
                "process_llm",
                "hitl_gate",
                "format_output"
            ],
            edges=[
                ("validate_input", "classify_intent"),
                ("classify_intent", "search_knowledge"),
                ("search_knowledge", "process_llm"),
                ("process_llm", "hitl_gate"),
                ("hitl_gate", "format_output"),
                ("format_output", "END")
            ],
            required_tools=["knowledge_base"],
            estimated_cost_per_run=0.03
        ))
        
        # 6. Content Generation Workflow
        self.register(WorkflowTemplate(
            name="Content Generation",
            type=WorkflowType.CONTENT_GENERATION,
            description="Generate and refine content with multiple review stages",
            config={
                "llm": {
                    "model": "gpt-4",
                    "temperature": 0.8
                },
                "generation": {
                    "max_drafts": 3,
                    "style_guide": True
                },
                "hitl": {
                    "enabled": True,
                    "threshold": 0.85,
                    "review_stages": ["draft", "final"]
                }
            },
            nodes=[
                "validate_input",
                "generate_outline",
                "generate_draft",
                "refine_content",
                "hitl_gate",
                "finalize",
                "format_output"
            ],
            edges=[
                ("validate_input", "generate_outline"),
                ("generate_outline", "generate_draft"),
                ("generate_draft", "refine_content"),
                ("refine_content", "hitl_gate"),
                ("hitl_gate", "finalize"),
                ("finalize", "format_output"),
                ("format_output", "END")
            ],
            estimated_cost_per_run=0.08
        ))
        
        # 7. Multi-Agent Workflow
        self.register(WorkflowTemplate(
            name="Multi-Agent Collaboration",
            type=WorkflowType.MULTI_AGENT,
            description="Multiple specialized agents working together",
            config={
                "agents": [
                    {"role": "researcher", "model": "gpt-4"},
                    {"role": "analyst", "model": "gpt-4"},
                    {"role": "writer", "model": "gpt-4"}
                ],
                "coordination": {
                    "strategy": "sequential",
                    "communication": "structured"
                },
                "hitl": {
                    "enabled": True,
                    "threshold": 0.75,
                    "review_points": ["after_research", "before_final"]
                }
            },
            nodes=[
                "validate_input",
                "agent_researcher",
                "agent_analyst",
                "hitl_gate_1",
                "agent_writer",
                "hitl_gate_2",
                "format_output"
            ],
            edges=[
                ("validate_input", "agent_researcher"),
                ("agent_researcher", "agent_analyst"),
                ("agent_analyst", "hitl_gate_1"),
                ("hitl_gate_1", "agent_writer"),
                ("agent_writer", "hitl_gate_2"),
                ("hitl_gate_2", "format_output"),
                ("format_output", "END")
            ],
            estimated_cost_per_run=0.25
        ))
    
    def register(self, template: WorkflowTemplate):
        """Register a workflow template"""
        self._templates[template.name] = template
        logger.info(f"Registered workflow template: {template.name}")
    
    def get(self, name: str) -> Optional[WorkflowTemplate]:
        """Get a workflow template by name"""
        return self._templates.get(name)
    
    def list(
        self,
        workflow_type: Optional[WorkflowType] = None,
        requires_hitl: Optional[bool] = None
    ) -> List[WorkflowTemplate]:
        """
        List workflow templates
        
        Args:
            workflow_type: Filter by workflow type
            requires_hitl: Filter by HITL requirement
            
        Returns:
            List of matching templates
        """
        templates = list(self._templates.values())
        
        if workflow_type:
            templates = [t for t in templates if t.type == workflow_type]
        
        if requires_hitl is not None:
            templates = [
                t for t in templates
                if t.config.get("hitl", {}).get("enabled", False) == requires_hitl
            ]
        
        return templates
    
    def create_from_template(
        self,
        template_name: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a workflow configuration from template
        
        Args:
            template_name: Name of the template
            custom_config: Custom configuration overrides
            
        Returns:
            Complete workflow configuration
        """
        template = self.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Start with template config
        config = template.config.copy()
        
        # Apply custom overrides
        if custom_config:
            self._deep_update(config, custom_config)
        
        workflow_config = {
            "name": template.name,
            "type": template.type.value,
            "description": template.description,
            "config": config,
            "workflow_definition": {
                "nodes": template.nodes,
                "edges": template.edges
            },
            "required_tools": template.required_tools or [],
            "recommended_llm": template.recommended_llm
        }
        
        logger.info(f"Created workflow from template: {template_name}")
        return workflow_config
    
    def _deep_update(self, base: dict, update: dict):
        """Deep update dictionary"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def export_template(self, template_name: str) -> str:
        """Export template as JSON"""
        import json
        template = self.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        return json.dumps(template.to_dict(), indent=2)
    
    def import_template(self, template_json: str):
        """Import template from JSON"""
        import json
        data = json.loads(template_json)
        
        template = WorkflowTemplate(
            name=data["name"],
            type=WorkflowType(data["type"]),
            description=data["description"],
            config=data["config"],
            nodes=data["nodes"],
            edges=[tuple(e) for e in data["edges"]],
            required_tools=data.get("required_tools"),
            recommended_llm=data.get("recommended_llm", "gpt-4"),
            estimated_cost_per_run=data.get("estimated_cost_per_run", 0.0)
        )
        
        self.register(template)
        logger.info(f"Imported workflow template: {template.name}")


# Global registry instance
_registry = WorkflowTemplateRegistry()


def get_workflow_registry() -> WorkflowTemplateRegistry:
    """Get global workflow template registry"""
    return _registry
