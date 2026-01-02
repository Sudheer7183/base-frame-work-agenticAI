"""
Self-Hosted LLM Cost Calculator - COMPLETE IMPLEMENTATION
Calculate infrastructure costs for self-hosted models

File: backend/app/services/self_hosted_calculator.py
Version: 2.0 COMPLETE
Author: Computational Audit Module
Date: 2025-12-31

INTEGRATION: Copy to backend/app/services/self_hosted_calculator.py
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.cost_tracker import AsyncCostTracker

logger = logging.getLogger(__name__)


class SelfHostedCostCalculator:
    """
    Calculate costs for self-hosted LLM models
    
    Tracks GPU infrastructure costs and compares with cloud pricing
    to provide ROI analysis for self-hosted deployments.
    
    Features:
    - GPU cost calculation by type
    - Cloud cost comparison
    - ROI analysis
    - Integration with AsyncCostTracker
    
    Supported GPU Types:
    - H100: $4.00/hr
    - A100: $2.50/hr
    - A10G: $1.00/hr
    - T4: $0.50/hr
    - V100: $1.50/hr
    - Custom: User-defined
    
    Usage:
        calculator = SelfHostedCostCalculator(db)
        
        result = await calculator.track_self_hosted_usage(
            execution_id="exec_123",
            agent_id=1,
            model_name="llama-2-70b",
            input_tokens=1000,
            output_tokens=500,
            inference_time_ms=2500,
            hardware_config={'gpu_type': 'A100', 'gpu_count': 4}
        )
    """
    
    # GPU hourly costs (USD)
    GPU_COSTS_PER_HOUR = {
        'H100': 4.00,
        'A100': 2.50,
        'A10G': 1.00,
        'T4': 0.50,
        'V100': 1.50,
        'A6000': 1.20,
        'RTX_4090': 0.80,
        'RTX_3090': 0.60
    }
    
    # Cloud equivalent pricing (per 1K tokens)
    CLOUD_EQUIVALENTS = {
        'llama-2-7b': {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'input': 0.0005, 'output': 0.0015},
        'llama-2-13b': {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'input': 0.0005, 'output': 0.0015},
        'llama-2-70b': {'provider': 'openai', 'model': 'gpt-4', 'input': 0.03, 'output': 0.06},
        'mistral-7b': {'provider': 'openai', 'model': 'gpt-3.5-turbo', 'input': 0.0005, 'output': 0.0015},
        'mixtral-8x7b': {'provider': 'openai', 'model': 'gpt-4', 'input': 0.03, 'output': 0.06},
        'codellama-34b': {'provider': 'openai', 'model': 'gpt-4', 'input': 0.03, 'output': 0.06}
    }
    
    def __init__(self, db: Session):
        """
        Initialize calculator
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.cost_tracker = AsyncCostTracker(db)
        logger.info("SelfHostedCostCalculator initialized")
    
    async def track_self_hosted_usage(
        self,
        execution_id: str,
        agent_id: int,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        inference_time_ms: int,
        hardware_config: Dict[str, Any],
        stage_name: str = "inference",
        node_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track self-hosted model usage
        
        Calculates infrastructure cost based on GPU type and usage,
        then tracks it via AsyncCostTracker.
        
        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            model_name: Model name (llama-2-70b, mistral-7b, etc.)
            input_tokens: Input token count
            output_tokens: Output token count
            inference_time_ms: Inference time in milliseconds
            hardware_config: Hardware configuration dict
                - gpu_type: GPU type (H100, A100, etc.)
                - gpu_count: Number of GPUs
                - memory_gb: GPU memory (optional)
                - custom_cost_per_hour: Custom hourly cost (optional)
            stage_name: Workflow stage
            node_name: LangGraph node name
            
        Returns:
            Dict with:
                - usage_id: ComputationalAuditUsage ID
                - infrastructure_cost: Infrastructure cost in USD
                - cost_per_hour: Calculated hourly cost
                - cloud_equivalent_cost: What this would cost in cloud
                - savings: How much saved vs cloud
                
        Example:
            result = await calculator.track_self_hosted_usage(
                execution_id="exec_123",
                agent_id=1,
                model_name="llama-2-70b",
                input_tokens=1000,
                output_tokens=500,
                inference_time_ms=2500,
                hardware_config={
                    'gpu_type': 'A100',
                    'gpu_count': 4,
                    'memory_gb': 320
                }
            )
            
            print(f"Infrastructure cost: ${result['infrastructure_cost']:.4f}")
            print(f"Cloud equivalent: ${result['cloud_equivalent_cost']:.4f}")
            print(f"Savings: ${result['savings']:.4f}")
        """
        try:
            # Calculate hardware cost
            cost_per_hour = self._calculate_hardware_cost(hardware_config)
            
            # Convert inference time to hours
            inference_hours = inference_time_ms / (1000 * 3600)
            
            # Calculate infrastructure cost
            infrastructure_cost = Decimal(str(cost_per_hour * inference_hours))
            
            # Track as LLM usage (with infrastructure cost as computed cost)
            usage = await self.cost_tracker.track_llm_usage(
                execution_id=execution_id,
                agent_id=agent_id,
                stage_name=stage_name,
                node_name=node_name,
                model_provider="self-hosted",
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=inference_time_ms,
                model_metadata=hardware_config
            )
            
            # Override computed cost with infrastructure cost
            if usage:
                def _update_cost():
                    usage.computed_cost_usd = infrastructure_cost
                    self.db.commit()
                
                await asyncio.to_thread(_update_cost)
            
            # Track infrastructure cost separately
            await self.cost_tracker.track_infrastructure_cost(
                execution_id,
                infrastructure_cost,
                f"{hardware_config.get('gpu_count', 1)}x {hardware_config.get('gpu_type', 'GPU')} for {inference_time_ms}ms"
            )
            
            # Calculate cloud equivalent cost
            cloud_cost = self._calculate_cloud_equivalent_cost(
                model_name,
                input_tokens,
                output_tokens
            )
            
            savings = cloud_cost - float(infrastructure_cost)
            
            logger.info(
                f"Tracked self-hosted: {model_name} on {hardware_config.get('gpu_type')}, "
                f"infra_cost=${infrastructure_cost:.4f}, cloud=${cloud_cost:.4f}, "
                f"savings=${savings:.4f}"
            )
            
            return {
                'usage_id': usage.id if usage else None,
                'infrastructure_cost': float(infrastructure_cost),
                'cost_per_hour': cost_per_hour,
                'cloud_equivalent_cost': cloud_cost,
                'savings': savings,
                'savings_percent': (savings / cloud_cost * 100) if cloud_cost > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error tracking self-hosted usage: {e}", exc_info=True)
            return {
                'usage_id': None,
                'infrastructure_cost': 0.0,
                'cost_per_hour': 0.0,
                'cloud_equivalent_cost': 0.0,
                'savings': 0.0,
                'error': str(e)
            }
    
    def _calculate_hardware_cost(self, hardware_config: Dict[str, Any]) -> float:
        """
        Calculate hourly hardware cost
        
        Args:
            hardware_config: Hardware configuration dict
                - gpu_type: GPU type
                - gpu_count: Number of GPUs
                - custom_cost_per_hour: Override cost (optional)
                
        Returns:
            Hourly cost in USD
        """
        # Use custom cost if provided
        if 'custom_cost_per_hour' in hardware_config:
            return float(hardware_config['custom_cost_per_hour'])
        
        gpu_type = hardware_config.get('gpu_type', 'A10G')
        gpu_count = hardware_config.get('gpu_count', 1)
        
        # Get base cost per GPU
        cost_per_gpu = self.GPU_COSTS_PER_HOUR.get(gpu_type, 1.00)
        
        # Calculate total cost
        # Add 20% overhead for power, cooling, networking
        total_cost = cost_per_gpu * gpu_count * 1.2
        
        logger.debug(
            f"Hardware cost: {gpu_count}x {gpu_type} @ ${cost_per_gpu}/hr "
            f"= ${total_cost:.2f}/hr (with 20% overhead)"
        )
        
        return total_cost
    
    def _calculate_cloud_equivalent_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate equivalent cloud cost
        
        Maps self-hosted models to equivalent cloud models and
        calculates what the same usage would cost in the cloud.
        
        Args:
            model_name: Self-hosted model name
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Equivalent cloud cost in USD
        """
        # Find cloud equivalent
        equivalent = None
        for key, equiv in self.CLOUD_EQUIVALENTS.items():
            if key in model_name.lower():
                equivalent = equiv
                break
        
        # Default to GPT-4 pricing if no match
        if not equivalent:
            logger.warning(f"No cloud equivalent for {model_name}, using GPT-4 pricing")
            equivalent = {'input': 0.03, 'output': 0.06}
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * equivalent['input']
        output_cost = (output_tokens / 1000) * equivalent['output']
        total_cost = input_cost + output_cost
        
        logger.debug(
            f"Cloud equivalent cost for {model_name}: "
            f"${total_cost:.6f} (input: ${input_cost:.6f}, output: ${output_cost:.6f})"
        )
        
        return total_cost
    
    async def compare_with_cloud(
        self,
        execution_id: str,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Compare self-hosted costs with cloud for an execution
        
        Aggregates all self-hosted usage for an execution and
        compares total cost with cloud equivalent.
        
        Args:
            execution_id: Execution ID
            model_name: Self-hosted model name
            
        Returns:
            Dict with:
                - total_infrastructure_cost: Total infra cost
                - total_cloud_cost: Total cloud equivalent cost
                - total_savings: Total savings
                - savings_percent: Savings percentage
                - recommendation: Cost-saving recommendation
                
        Example:
            comparison = await calculator.compare_with_cloud(
                execution_id="exec_123",
                model_name="llama-2-70b"
            )
            
            if comparison['total_savings'] > 0:
                print(f"Self-hosted saved ${comparison['total_savings']:.2f}")
            else:
                print(f"Cloud would save ${-comparison['total_savings']:.2f}")
        """
        try:
            def _get_costs():
                from app.models.computational_audit import ComputationalAuditUsage
                
                # Get all self-hosted usage for this execution
                usages = self.db.query(ComputationalAuditUsage).filter(
                    ComputationalAuditUsage.execution_id == execution_id,
                    ComputationalAuditUsage.model_provider == 'self-hosted'
                ).all()
                
                total_infra_cost = sum(float(u.computed_cost_usd) for u in usages)
                
                # Calculate cloud equivalent for each usage
                total_cloud_cost = 0.0
                for usage in usages:
                    cloud_cost = self._calculate_cloud_equivalent_cost(
                        usage.model_name,
                        usage.input_tokens,
                        usage.output_tokens
                    )
                    total_cloud_cost += cloud_cost
                
                return total_infra_cost, total_cloud_cost
            
            total_infra, total_cloud = await asyncio.to_thread(_get_costs)
            
            savings = total_cloud - total_infra
            savings_percent = (savings / total_cloud * 100) if total_cloud > 0 else 0
            
            # Generate recommendation
            if savings > 0:
                recommendation = f"Self-hosted is more cost-effective (${savings:.2f} saved)"
            elif savings < -10:
                recommendation = f"Cloud would be more cost-effective (${-savings:.2f} cheaper)"
            else:
                recommendation = "Costs are roughly equivalent"
            
            return {
                'total_infrastructure_cost': total_infra,
                'total_cloud_cost': total_cloud,
                'total_savings': savings,
                'savings_percent': savings_percent,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error comparing with cloud: {e}", exc_info=True)
            return {
                'error': str(e)
            }
    
    def add_custom_gpu_pricing(self, gpu_type: str, cost_per_hour: float):
        """
        Add custom GPU pricing
        
        Allows defining pricing for GPU types not in the default list.
        
        Args:
            gpu_type: GPU type name
            cost_per_hour: Hourly cost in USD
            
        Example:
            calculator.add_custom_gpu_pricing('RTX_5090', 1.50)
        """
        self.GPU_COSTS_PER_HOUR[gpu_type] = cost_per_hour
        logger.info(f"Added custom GPU pricing: {gpu_type} @ ${cost_per_hour}/hr")
    
    def add_cloud_equivalent(
        self,
        model_name: str,
        provider: str,
        cloud_model: str,
        input_cost: float,
        output_cost: float
    ):
        """
        Add cloud equivalent pricing
        
        Allows defining cloud equivalents for custom models.
        
        Args:
            model_name: Self-hosted model name
            provider: Cloud provider
            cloud_model: Cloud model name
            input_cost: Input cost per 1K tokens
            output_cost: Output cost per 1K tokens
            
        Example:
            calculator.add_cloud_equivalent(
                'custom-llm-7b',
                'openai',
                'gpt-3.5-turbo',
                0.0005,
                0.0015
            )
        """
        self.CLOUD_EQUIVALENTS[model_name] = {
            'provider': provider,
            'model': cloud_model,
            'input': input_cost,
            'output': output_cost
        }
        logger.info(f"Added cloud equivalent: {model_name} -> {provider}:{cloud_model}")


# Import asyncio here to avoid circular import
import asyncio

# END OF FILE - SelfHostedCostCalculator complete (425 lines)
