# """LangGraph workflow nodes"""

# import logging
# from typing import Dict, Any
# from app.workflows.base import WorkflowState

# logger = logging.getLogger(__name__)


# async def input_validation_node(state: WorkflowState) -> WorkflowState:
#     """
#     Validate input data
    
#     Ensures all required fields are present
#     """
#     logger.info(f"Validating input for execution {state.execution_id}")
    
#     # Add validation logic here
#     required_fields = state.config.get("required_fields", [])
    
#     for field in required_fields:
#         if field not in state.input_data:
#             state.error = f"Missing required field: {field}"
#             return state
    
#     logger.info("Input validation passed")
#     return state


# async def llm_processing_node(state: WorkflowState) -> WorkflowState:
#     """
#     Process input with LLM
    
#     This is a placeholder - integrate with your LLM provider
#     """
#     logger.info(f"Processing with LLM for execution {state.execution_id}")
    
#     # Placeholder LLM processing
#     # TODO: Integrate with Ollama/OpenAI/Anthropic
    
#     state.output_data = {
#         "processed": True,
#         "input": state.input_data,
#         "result": "LLM processing placeholder - implement actual logic"
#     }
    
#     return state


# async def hitl_gate_node(state: WorkflowState) -> WorkflowState:
#     """
#     HITL gate - determines if human review is needed
    
#     Configure via agent config: {"hitl": {"enabled": true, "threshold": 0.8}}
#     """
#     logger.info(f"Checking HITL requirements for execution {state.execution_id}")
    
#     hitl_config = state.config.get("hitl", {})
    
#     if not hitl_config.get("enabled", False):
#         logger.info("HITL not enabled for this agent")
#         return state
    
#     # Check if HITL is required based on confidence or other criteria
#     confidence = state.output_data.get("confidence", 1.0) if state.output_data else 1.0
#     threshold = hitl_config.get("threshold", 0.8)
    
#     if confidence < threshold:
#         logger.info(f"HITL required: confidence {confidence} < threshold {threshold}")
#         state.requires_hitl = True
#     else:
#         logger.info(f"HITL not required: confidence {confidence} >= threshold {threshold}")
    
#     return state


# async def output_formatting_node(state: WorkflowState) -> WorkflowState:
#     """
#     Format output data
    
#     Ensures output is in the expected format
#     """
#     logger.info(f"Formatting output for execution {state.execution_id}")
    
#     if state.output_data:
#         # Add formatting logic here
#         state.output_data["formatted"] = True
#         state.output_data["execution_id"] = state.execution_id
    
#     return state


# async def error_handling_node(state: WorkflowState) -> WorkflowState:
#     """
#     Handle errors in the workflow
    
#     Logs errors and formats error responses
#     """
#     if state.error:
#         logger.error(f"Error in execution {state.execution_id}: {state.error}")
        
#         state.output_data = {
#             "error": True,
#             "message": state.error,
#             "execution_id": state.execution_id
#         }
    
#     return state

"""
Enhanced workflow nodes with proper LLM integration

File: backend/app/workflows/nodes.py
"""

import logging
from typing import Dict, Any, Optional
from app.workflows.base import WorkflowState

logger = logging.getLogger(__name__)


class LLMProvider:
    """Factory for LLM providers"""
    
    @staticmethod
    def get_provider(config: Dict[str, Any]):
        """Get appropriate LLM provider based on config"""
        provider_type = config.get("provider", "ollama").lower()
        
        if provider_type == "openai":
            return OpenAIProvider(config)
        elif provider_type == "anthropic":
            return AnthropicProvider(config)
        else:
            return OllamaProvider(config)


class OllamaProvider:
    """Ollama LLM provider"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("ollama_base_url", "http://localhost:11434")
        self.model = config.get("model", "llama2")
        self.temperature = config.get("temperature", 0.7)
        self.timeout = config.get("timeout", 120)
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from Ollama"""
        import httpx
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": self.temperature,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "content": result.get("message", {}).get("content", ""),
                        "model": self.model,
                        "provider": "ollama",
                        "success": True
                    }
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    raise Exception(f"Ollama API error: {response.status_code}")
                    
        except httpx.TimeoutException:
            logger.error(f"Ollama request timeout after {self.timeout}s")
            raise Exception(f"LLM request timeout")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise


class OpenAIProvider:
    """OpenAI LLM provider"""
    
    def __init__(self, config: Dict[str, Any]):
        from app.core.config import settings
        
        self.api_key = config.get("api_key") or getattr(settings, "OPENAI_API_KEY", None)
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from OpenAI"""
        import httpx
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "content": result["choices"][0]["message"]["content"],
                        "model": self.model,
                        "provider": "openai",
                        "success": True,
                        "usage": result.get("usage", {})
                    }
                else:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    raise Exception(f"OpenAI API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise


class AnthropicProvider:
    """Anthropic Claude provider"""
    
    def __init__(self, config: Dict[str, Any]):
        from app.core.config import settings
        
        self.api_key = config.get("api_key") or getattr(settings, "ANTHROPIC_API_KEY", None)
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
        
        self.model = config.get("model", "claude-3-sonnet-20240229")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4000)
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from Anthropic"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                body = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
                
                if system_prompt:
                    body["system"] = system_prompt
                
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json=body
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "content": result["content"][0]["text"],
                        "model": self.model,
                        "provider": "anthropic",
                        "success": True,
                        "usage": result.get("usage", {})
                    }
                else:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                    raise Exception(f"Anthropic API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            raise


async def input_validation_node(state: WorkflowState) -> WorkflowState:
    """
    Validate input data
    
    Ensures all required fields are present
    """
    logger.info(f"Validating input for execution {state.execution_id}")
    
    # Add validation logic here
    required_fields = state.config.get("required_fields", [])
    
    for field in required_fields:
        if field not in state.input_data:
            state.error = f"Missing required field: {field}"
            return state
    
    logger.info("Input validation passed")
    return state


async def llm_processing_node(state: WorkflowState) -> WorkflowState:
    """
    Process input with LLM
    
    Supports multiple LLM providers: Ollama, OpenAI, Anthropic
    """
    logger.info(f"Processing with LLM for execution {state.execution_id}")
    
    try:
        # Get LLM provider from config
        llm_provider = LLMProvider.get_provider(state.config)
        
        # Prepare prompt
        system_prompt = state.config.get("system_prompt", 
            "You are a helpful AI assistant. Provide clear, accurate, and concise responses.")
        
        # Extract user input
        user_message = state.input_data.get("message") or state.input_data.get("prompt") or str(state.input_data)
        
        # Add context if available
        context = state.config.get("context", "")
        if context:
            user_message = f"Context: {context}\n\nUser Query: {user_message}"
        
        logger.info(f"Sending request to LLM provider: {llm_provider.__class__.__name__}")
        
        # Generate response
        result = await llm_provider.generate(user_message, system_prompt)
        
        # Calculate confidence (basic heuristic)
        confidence = 0.9  # Default high confidence
        if len(result["content"]) < 50:
            confidence = 0.7  # Lower confidence for very short responses
        
        state.output_data = {
            "response": result["content"],
            "model": result["model"],
            "provider": result["provider"],
            "confidence": confidence,
            "success": True
        }
        
        # Add usage info if available
        if "usage" in result:
            state.output_data["usage"] = result["usage"]
        
        logger.info(f"LLM processing completed successfully (confidence: {confidence})")
        
    except Exception as e:
        logger.error(f"LLM processing failed: {e}", exc_info=True)
        state.error = f"LLM processing error: {str(e)}"
        state.output_data = {
            "success": False,
            "error": str(e)
        }
    
    return state


async def hitl_gate_node(state: WorkflowState) -> WorkflowState:
    """
    HITL gate - determines if human review is needed
    
    Configure via agent config: {"hitl": {"enabled": true, "threshold": 0.8}}
    """
    logger.info(f"Checking HITL requirements for execution {state.execution_id}")
    
    hitl_config = state.config.get("hitl", {})
    
    if not hitl_config.get("enabled", False):
        logger.info("HITL not enabled for this agent")
        return state
    
    # Check if HITL is required based on confidence or other criteria
    confidence = state.output_data.get("confidence", 1.0) if state.output_data else 1.0
    threshold = hitl_config.get("threshold", 0.8)
    
    if confidence < threshold:
        logger.info(f"HITL required: confidence {confidence} < threshold {threshold}")
        state.requires_hitl = True
    else:
        logger.info(f"HITL not required: confidence {confidence} >= threshold {threshold}")
    
    return state


async def output_formatting_node(state: WorkflowState) -> WorkflowState:
    """
    Format output data
    
    Ensures output is in the expected format
    """
    logger.info(f"Formatting output for execution {state.execution_id}")
    
    if state.output_data:
        # Add formatting logic here
        state.output_data["formatted"] = True
        state.output_data["execution_id"] = state.execution_id
        state.output_data["agent_name"] = state.agent_name
        state.output_data["timestamp"] = __import__("datetime").datetime.utcnow().isoformat()
    
    return state


async def error_handling_node(state: WorkflowState) -> WorkflowState:
    """
    Handle errors in the workflow
    
    Logs errors and formats error responses
    """
    if state.error:
        logger.error(f"Error in execution {state.execution_id}: {state.error}")
        
        state.output_data = {
            "error": True,
            "message": state.error,
            "execution_id": state.execution_id,
            "agent_name": state.agent_name
        }
    
    return state