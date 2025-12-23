"""
Tool Registry and Execution Framework
Manages tool definitions, registration, and execution
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Tool definition metadata"""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str
    version: str = "1.0.0"
    enabled: bool = True
    timeout_seconds: int = 30
    requires_auth: bool = False


class BaseTool(ABC):
    """
    Base class for all tools
    
    Subclass this to create custom tools
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.execution_count = 0
        self.last_execution = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool with given parameters
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Get tool definition for registration"""
        pass
    
    async def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters
        
        Override for custom validation
        """
        return True
    
    async def on_success(self, result: Any) -> None:
        """Hook called after successful execution"""
        self.execution_count += 1
        self.last_execution = datetime.utcnow()
        logger.info(f"Tool {self.name} executed successfully")
    
    async def on_error(self, error: Exception) -> None:
        """Hook called after failed execution"""
        logger.error(f"Tool {self.name} failed: {error}")


class ToolRegistry:
    """
    Centralized tool registry
    
    Manages tool registration, discovery, and execution
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._definitions: Dict[str, ToolDefinition] = {}
        logger.info("Tool registry initialized")
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool
        
        Args:
            tool: Tool instance to register
        """
        definition = tool.get_definition()
        
        if definition.name in self._tools:
            logger.warning(f"Tool {definition.name} already registered, overwriting")
        
        self._tools[definition.name] = tool
        self._definitions[definition.name] = definition
        
        logger.info(f"Registered tool: {definition.name} v{definition.version}")
    
    def unregister(self, tool_name: str) -> None:
        """Unregister a tool"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._definitions[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a registered tool by name"""
        return self._tools.get(tool_name)
    
    def get_definition(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name"""
        return self._definitions.get(tool_name)
    
    def list_tools(self, category: Optional[str] = None, enabled_only: bool = True) -> List[ToolDefinition]:
        """
        List all registered tools
        
        Args:
            category: Filter by category
            enabled_only: Only return enabled tools
            
        Returns:
            List of tool definitions
        """
        definitions = list(self._definitions.values())
        
        if category:
            definitions = [d for d in definitions if d.category == category]
        
        if enabled_only:
            definitions = [d for d in definitions if d.enabled]
        
        return definitions
    
    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            timeout: Execution timeout in seconds
            
        Returns:
            Execution result with metadata
        """
        tool = self.get_tool(tool_name)
        definition = self.get_definition(tool_name)
        
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        if not definition.enabled:
            raise ValueError(f"Tool disabled: {tool_name}")
        
        start_time = datetime.utcnow()
        execution_timeout = timeout or definition.timeout_seconds
        
        try:
            # Validate input
            if not await tool.validate_input(**parameters):
                raise ValueError(f"Invalid parameters for tool: {tool_name}")
            
            # Execute with timeout
            result = await asyncio.wait_for(
                tool.execute(**parameters),
                timeout=execution_timeout
            )
            
            # Success hook
            await tool.on_success(result)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Tool execution timeout after {execution_timeout}s"
            logger.error(f"{tool_name}: {error_msg}")
            await tool.on_error(TimeoutError(error_msg))
            
            return {
                "success": False,
                "tool": tool_name,
                "error": error_msg,
                "error_type": "timeout",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"{tool_name} execution failed: {error_msg}", exc_info=True)
            await tool.on_error(e)
            
            return {
                "success": False,
                "tool": tool_name,
                "error": error_msg,
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            }


# Global registry instance
_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    return _registry


# Example tool implementations
class SearchTool(BaseTool):
    """Example: Web search tool"""
    
    async def execute(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Execute search"""
        # TODO: Implement actual search logic
        return {
            "query": query,
            "results": [
                {"title": "Result 1", "url": "https://example.com/1"},
                {"title": "Result 2", "url": "https://example.com/2"}
            ][:max_results]
        }
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search",
            description="Search the web for information",
            parameters={
                "query": {"type": "string", "required": True},
                "max_results": {"type": "integer", "default": 10}
            },
            category="search",
            timeout_seconds=30
        )


class CalculatorTool(BaseTool):
    """Example: Calculator tool"""
    
    async def execute(self, expression: str) -> Dict[str, Any]:
        """Evaluate mathematical expression"""
        try:
            # Simple eval - in production use a safe expression evaluator
            result = eval(expression, {"__builtins__": {}}, {})
            return {"expression": expression, "result": result}
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calculator",
            description="Perform mathematical calculations",
            parameters={
                "expression": {"type": "string", "required": True}
            },
            category="utility",
            timeout_seconds=5
        )


class DatabaseQueryTool(BaseTool):
    """Example: Database query tool"""
    
    async def execute(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query database"""
        # TODO: Implement actual database query
        return [
            {"id": 1, "name": "Record 1"},
            {"id": 2, "name": "Record 2"}
        ]
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="database_query",
            description="Query database tables",
            parameters={
                "table": {"type": "string", "required": True},
                "filters": {"type": "object", "required": False}
            },
            category="database",
            requires_auth=True,
            timeout_seconds=60
        )


# Auto-register example tools
def register_default_tools():
    """Register default tools"""
    registry = get_tool_registry()
    registry.register(SearchTool())
    registry.register(CalculatorTool())
    registry.register(DatabaseQueryTool())
    logger.info("Default tools registered")
