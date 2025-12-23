"""
AI Model Management Module
Centralized management of LLM models, configurations, and providers
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, Text, DateTime
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import httpx

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.base import Base
from sqlalchemy.dialects.postgresql import JSONB

# ============================================================================
# Enums
# ============================================================================

class ModelProvider(str, Enum):
    """Supported AI model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    AWS_BEDROCK = "aws_bedrock"


class ModelCapability(str, Enum):
    """Model capabilities"""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    CODE_GENERATION = "code_generation"
    EMBEDDINGS = "embeddings"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    AUDIO = "audio"


class ModelStatus(str, Enum):
    """Model availability status"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    UNAVAILABLE = "unavailable"
    BETA = "beta"


# ============================================================================
# Database Models
# ============================================================================

class AIModel(Base):
    """AI Model registry"""
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Model identification
    name = Column(String(255), nullable=False, index=True)
    model_id = Column(String(255), nullable=False, unique=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    version = Column(String(50), nullable=True)
    
    # Model details
    description = Column(Text, nullable=True)
    capabilities = Column(JSON, nullable=False, default=[])
    context_window = Column(Integer, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    
    # Pricing (per 1M tokens)
    input_cost_per_1m = Column(Float, nullable=True)
    output_cost_per_1m = Column(Float, nullable=True)
    
    # Performance metrics
    avg_latency_ms = Column(Float, nullable=True)
    throughput_tokens_per_sec = Column(Float, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False, default=ModelStatus.ACTIVE.value, index=True)
    is_default = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True, index=True)
    
    # Configuration
    default_parameters = Column(JSON, nullable=False, default={
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1.0
    })
    
    # Metadata
    tags = Column(JSON, nullable=False, default=[])
    event_metadata = Column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelConfiguration(Base):
    """Model configuration per tenant/agent"""
    __tablename__ = "model_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_slug = Column(String(100), nullable=False, index=True)
    
    # Reference
    model_id = Column(Integer, nullable=False, index=True)
    agent_id = Column(Integer, nullable=True, index=True)  # NULL = tenant-wide default
    
    # Configuration
    parameters = Column(JSON, nullable=False, default={})
    
    # API Configuration
    api_endpoint = Column(String(500), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)  # Encrypted API key
    
    # Rate limiting
    max_requests_per_minute = Column(Integer, nullable=True)
    max_tokens_per_day = Column(Integer, nullable=True)
    
    # Fallback configuration
    fallback_model_id = Column(Integer, nullable=True)
    retry_attempts = Column(Integer, default=3)
    
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelUsage(Base):
    """Track model usage for billing and analytics"""
    __tablename__ = "model_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_slug = Column(String(100), nullable=False, index=True)
    
    # References
    model_id = Column(Integer, nullable=False, index=True)
    agent_id = Column(Integer, nullable=True, index=True)
    execution_id = Column(String(255), nullable=True, index=True)
    
    # Usage metrics
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    
    # Cost
    cost_usd = Column(Float, nullable=False, default=0.0)
    
    # Performance
    latency_ms = Column(Float, nullable=True)
    
    # Status
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(String(500), nullable=True)
    
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class AIModelBase(BaseModel):
    """Base AI model schema"""
    name: str = Field(..., max_length=255)
    model_id: str = Field(..., max_length=255)
    provider: ModelProvider
    version: Optional[str] = None
    description: Optional[str] = None
    capabilities: List[ModelCapability] = Field(default_factory=list)
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    input_cost_per_1m: Optional[float] = None
    output_cost_per_1m: Optional[float] = None
    default_parameters: Dict[str, Any] = Field(default_factory=lambda: {
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1.0
    })
    tags: List[str] = Field(default_factory=list)


class AIModelCreate(AIModelBase):
    """Create AI model"""
    status: ModelStatus = ModelStatus.ACTIVE
    is_enabled: bool = True


class AIModelResponse(AIModelBase):
    """AI model response"""
    id: int
    status: str
    is_default: bool
    is_enabled: bool
    avg_latency_ms: Optional[float]
    throughput_tokens_per_sec: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelConfigurationCreate(BaseModel):
    """Create model configuration"""
    model_id: int
    agent_id: Optional[int] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    max_requests_per_minute: Optional[int] = None
    max_tokens_per_day: Optional[int] = None
    fallback_model_id: Optional[int] = None
    retry_attempts: int = 3


class ModelConfigurationResponse(BaseModel):
    """Model configuration response"""
    id: int
    tenant_slug: str
    model_id: int
    agent_id: Optional[int]
    parameters: Dict[str, Any]
    max_requests_per_minute: Optional[int]
    max_tokens_per_day: Optional[int]
    fallback_model_id: Optional[int]
    retry_attempts: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ModelUsageStats(BaseModel):
    """Model usage statistics"""
    model_id: int
    model_name: str
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    success_rate: float


class ModelComparisonResult(BaseModel):
    """Model comparison result"""
    models: List[Dict[str, Any]]
    comparison_metrics: List[str]
    recommendation: Optional[str] = None


class ModelTestRequest(BaseModel):
    """Request to test a model"""
    model_id: int
    prompt: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ModelTestResponse(BaseModel):
    """Model test response"""
    success: bool
    response_text: Optional[str] = None
    latency_ms: float
    tokens_used: int
    cost_usd: float
    error: Optional[str] = None


# ============================================================================
# Model Management Service
# ============================================================================

class ModelManagementService:
    """Service for managing AI models"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_model(self, model_id: int) -> Optional[AIModel]:
        """Get model by ID"""
        return self.db.query(AIModel).filter(AIModel.id == model_id).first()
    
    def list_models(
        self,
        provider: Optional[ModelProvider] = None,
        capability: Optional[ModelCapability] = None,
        status: Optional[ModelStatus] = None,
        is_enabled: Optional[bool] = None
    ) -> List[AIModel]:
        """List models with filters"""
        query = self.db.query(AIModel)
        
        if provider:
            query = query.filter(AIModel.provider == provider.value)
        
        if capability:
            query = query.filter(AIModel.capabilities.contains([capability.value]))
        
        if status:
            query = query.filter(AIModel.status == status.value)
        
        if is_enabled is not None:
            query = query.filter(AIModel.is_enabled == is_enabled)
        
        return query.order_by(AIModel.provider, AIModel.name).all()
    
    def create_model(self, model: AIModelCreate) -> AIModel:
        """Register a new model"""
        db_model = AIModel(**model.dict())
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return db_model
    
    def update_model(self, model_id: int, updates: Dict[str, Any]) -> AIModel:
        """Update model configuration"""
        model = self.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        self.db.commit()
        self.db.refresh(model)
        return model
    
    def get_model_config(
        self,
        tenant_slug: str,
        model_id: int,
        agent_id: Optional[int] = None
    ) -> Optional[ModelConfiguration]:
        """Get model configuration for tenant/agent"""
        query = self.db.query(ModelConfiguration).filter(
            ModelConfiguration.tenant_slug == tenant_slug,
            ModelConfiguration.model_id == model_id,
            ModelConfiguration.is_active == True
        )
        
        if agent_id:
            query = query.filter(ModelConfiguration.agent_id == agent_id)
        else:
            query = query.filter(ModelConfiguration.agent_id.is_(None))
        
        return query.first()
    
    def get_usage_stats(
        self,
        tenant_slug: str,
        model_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> ModelUsageStats:
        """Get usage statistics for a model"""
        from sqlalchemy import func
        
        model = self.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        usage = self.db.query(
            func.count(ModelUsage.id).label('total_requests'),
            func.sum(ModelUsage.input_tokens).label('total_input'),
            func.sum(ModelUsage.output_tokens).label('total_output'),
            func.sum(ModelUsage.cost_usd).label('total_cost'),
            func.avg(ModelUsage.latency_ms).label('avg_latency'),
            func.sum(func.cast(ModelUsage.success, Integer)).label('successful')
        ).filter(
            ModelUsage.tenant_slug == tenant_slug,
            ModelUsage.model_id == model_id,
            ModelUsage.timestamp >= start_date,
            ModelUsage.timestamp <= end_date
        ).first()
        
        total = usage.total_requests or 0
        successful = usage.successful or 0
        
        return ModelUsageStats(
            model_id=model_id,
            model_name=model.name,
            total_requests=total,
            total_input_tokens=int(usage.total_input or 0),
            total_output_tokens=int(usage.total_output or 0),
            total_cost_usd=float(usage.total_cost or 0),
            avg_latency_ms=float(usage.avg_latency or 0),
            success_rate=successful / total * 100 if total > 0 else 0.0
        )
    
    async def test_model(
        self,
        model_id: int,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> ModelTestResponse:
        """Test a model with a sample prompt"""
        model = self.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        start_time = datetime.utcnow()
        
        try:
            # This is a simplified example - implement actual API calls
            # based on the provider
            
            if model.provider == ModelProvider.OPENAI.value:
                response_text = "Test response from OpenAI"
                tokens_used = 50
            
            elif model.provider == ModelProvider.ANTHROPIC.value:
                response_text = "Test response from Anthropic"
                tokens_used = 50
            
            elif model.provider == ModelProvider.OLLAMA.value:
                response_text = "Test response from Ollama"
                tokens_used = 50
            
            else:
                response_text = "Test response (mock)"
                tokens_used = 50
            
            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000
            
            # Calculate cost
            cost = 0.0
            if model.input_cost_per_1m and model.output_cost_per_1m:
                cost = (tokens_used / 1_000_000) * (model.input_cost_per_1m + model.output_cost_per_1m) / 2
            
            return ModelTestResponse(
                success=True,
                response_text=response_text,
                latency_ms=latency,
                tokens_used=tokens_used,
                cost_usd=cost
            )
        
        except Exception as e:
            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000
            
            return ModelTestResponse(
                success=False,
                latency_ms=latency,
                tokens_used=0,
                cost_usd=0.0,
                error=str(e)
            )
    
    def compare_models(
        self,
        model_ids: List[int],
        tenant_slug: str,
        start_date: datetime,
        end_date: datetime
    ) -> ModelComparisonResult:
        """Compare multiple models"""
        comparisons = []
        
        for model_id in model_ids:
            stats = self.get_usage_stats(tenant_slug, model_id, start_date, end_date)
            model = self.get_model(model_id)
            
            comparisons.append({
                "model_id": model_id,
                "model_name": model.name,
                "provider": model.provider,
                "avg_latency_ms": stats.avg_latency_ms,
                "success_rate": stats.success_rate,
                "total_cost": stats.total_cost_usd,
                "cost_per_1k_tokens": (stats.total_cost_usd / (stats.total_input_tokens + stats.total_output_tokens)) * 1000 if (stats.total_input_tokens + stats.total_output_tokens) > 0 else 0
            })
        
        # Simple recommendation logic
        if comparisons:
            best = min(comparisons, key=lambda x: x['cost_per_1k_tokens'] if x['success_rate'] > 95 else float('inf'))
            recommendation = f"Based on cost and reliability, {best['model_name']} is recommended"
        else:
            recommendation = None
        
        return ModelComparisonResult(
            models=comparisons,
            comparison_metrics=["avg_latency_ms", "success_rate", "total_cost", "cost_per_1k_tokens"],
            recommendation=recommendation
        )


# ============================================================================
# API Router
# ============================================================================

router = APIRouter(prefix="/models", tags=["AI Model Management"])


@router.get("/", response_model=List[AIModelResponse])
async def list_models(
    provider: Optional[ModelProvider] = Query(None),
    capability: Optional[ModelCapability] = Query(None),
    status: Optional[ModelStatus] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all available AI models"""
    service = ModelManagementService(db)
    models = service.list_models(provider, capability, status, is_enabled)
    return models


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Get details of a specific model"""
    service = ModelManagementService(db)
    model = service.get_model(model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model


@router.post("/", response_model=AIModelResponse)
async def create_model(
    model: AIModelCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Register a new AI model"""
    service = ModelManagementService(db)
    return service.create_model(model)


@router.put("/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: int,
    updates: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Update model configuration"""
    service = ModelManagementService(db)
    return service.update_model(model_id, updates)


@router.post("/configurations", response_model=ModelConfigurationResponse)
async def create_model_configuration(
    tenant_slug: str,
    config: ModelConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Create model configuration for tenant/agent"""
    # Encrypt API key before storing
    encrypted_key = config.api_key  # TODO: Implement encryption
    
    db_config = ModelConfiguration(
        tenant_slug=tenant_slug,
        model_id=config.model_id,
        agent_id=config.agent_id,
        parameters=config.parameters,
        api_endpoint=config.api_endpoint,
        api_key_encrypted=encrypted_key,
        max_requests_per_minute=config.max_requests_per_minute,
        max_tokens_per_day=config.max_tokens_per_day,
        fallback_model_id=config.fallback_model_id,
        retry_attempts=config.retry_attempts
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config


@router.get("/{model_id}/usage", response_model=ModelUsageStats)
async def get_model_usage(
    model_id: int,
    tenant_slug: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get usage statistics for a model"""
    service = ModelManagementService(db)
    return service.get_usage_stats(tenant_slug, model_id, start_date, end_date)


@router.post("/test", response_model=ModelTestResponse)
async def test_model(
    request: ModelTestRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Test a model with a sample prompt"""
    service = ModelManagementService(db)
    return await service.test_model(request.model_id, request.prompt, request.parameters)


@router.post("/compare", response_model=ModelComparisonResult)
async def compare_models(
    model_ids: List[int],
    tenant_slug: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Compare multiple models"""
    service = ModelManagementService(db)
    return service.compare_models(model_ids, tenant_slug, start_date, end_date)


@router.get("/providers/list", response_model=List[str])
async def list_providers():
    """List all supported model providers"""
    return [p.value for p in ModelProvider]


@router.get("/capabilities/list", response_model=List[str])
async def list_capabilities():
    """List all model capabilities"""
    return [c.value for c in ModelCapability]
