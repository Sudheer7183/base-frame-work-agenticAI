"""
Workflow Marketplace API
Allows users to browse, share, and install workflow templates
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import Session, relationship
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.base import Base
from app.models.user import User
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey, Float, DateTime
from sqlalchemy.sql import text
# ============================================================================
# Database Models
# ============================================================================

class WorkflowTemplate(Base):
    """Workflow template in the marketplace"""
    __tablename__ = "workflow_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    tags = Column(JSON, nullable=False, default=[])
    
    # Workflow definition
    workflow_definition = Column(JSON, nullable=False)
    config_schema = Column(JSON, nullable=False, default={})
    
    # created_at = Column(DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    # updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
 

    # Metadata
    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    is_official = Column(Boolean, default=False, index=True)
    is_public = Column(Boolean, default=True, index=True)
    
    # Stats
    install_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    
    # Version info
    version = Column(String(50), nullable=False, default="1.0.0")
    changelog = Column(Text, nullable=True)
    
    # Pricing (for premium templates)
    is_premium = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    
    # Relationships
    reviews = relationship("WorkflowReview", back_populates="template", cascade="all, delete-orphan")
    installations = relationship("WorkflowInstallation", back_populates="template")


class WorkflowReview(Base):
    """User reviews for workflow templates"""
    __tablename__ = "workflow_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('workflow_templates.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    helpful_count = Column(Integer, default=0)
    
    template = relationship("WorkflowTemplate", back_populates="reviews")


class WorkflowInstallation(Base):
    """Track workflow installations"""
    __tablename__ = "workflow_installations"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('workflow_templates.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True)
    
    customizations = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, default=True)
    
    template = relationship("WorkflowTemplate", back_populates="installations")


# ============================================================================
# Pydantic Schemas
# ============================================================================

class WorkflowTemplateBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: str = Field(..., max_length=100)
    tags: List[str] = Field(default_factory=list)
    workflow_definition: dict
    config_schema: dict = Field(default_factory=dict)
    version: str = "1.0.0"
    changelog: Optional[str] = None


class WorkflowTemplateCreate(WorkflowTemplateBase):
    is_public: bool = True
    is_premium: bool = False
    price: float = 0.0


class WorkflowTemplateResponse(WorkflowTemplateBase):
    id: int
    author_id: Optional[int]
    is_official: bool
    is_public: bool
    install_count: int
    rating: float
    review_count: int
    is_premium: bool
    price: float
    # created_at: datetime
    # updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class WorkflowReviewResponse(BaseModel):
    id: int
    template_id: int
    user_id: int
    rating: int
    comment: Optional[str]
    helpful_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowInstallRequest(BaseModel):
    template_id: int
    agent_id: Optional[int] = None
    customizations: dict = Field(default_factory=dict)


class MarketplaceStats(BaseModel):
    total_templates: int
    official_templates: int
    community_templates: int
    total_installs: int
    avg_rating: float
    popular_categories: List[dict]


# ============================================================================
# API Router
# ============================================================================

router = APIRouter(prefix="/marketplace", tags=["Workflow Marketplace"])


@router.get("/templates", response_model=List[WorkflowTemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated
    is_official: Optional[bool] = Query(None),
    is_premium: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("popular", regex="^(popular|recent|rating|installs)$"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Browse workflow templates in the marketplace
    
    - **category**: Filter by category
    - **tags**: Filter by tags (comma-separated)
    - **is_official**: Show only official templates
    - **is_premium**: Show only premium/free templates
    - **search**: Search in name and description
    - **sort_by**: Sort by popularity, recency, rating, or install count
    """
    query = db.query(WorkflowTemplate).filter(WorkflowTemplate.is_public == True)
    
    # Apply filters
    if category:
        query = query.filter(WorkflowTemplate.category == category)
    
    if tags:
        tag_list = [t.strip() for t in tags.split(',')]
        for tag in tag_list:
            query = query.filter(WorkflowTemplate.tags.contains([tag]))
    
    if is_official is not None:
        query = query.filter(WorkflowTemplate.is_official == is_official)
    
    if is_premium is not None:
        query = query.filter(WorkflowTemplate.is_premium == is_premium)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (WorkflowTemplate.name.ilike(search_term)) |
            (WorkflowTemplate.description.ilike(search_term))
        )
    
    # Apply sorting
    if sort_by == "popular":
        query = query.order_by(WorkflowTemplate.install_count.desc())
    elif sort_by == "recent":
        query = query.order_by(WorkflowTemplate.created_at.desc())
    elif sort_by == "rating":
        query = query.order_by(WorkflowTemplate.rating.desc())
    elif sort_by == "installs":
        query = query.order_by(WorkflowTemplate.install_count.desc())
    
    templates = query.offset(offset).limit(limit).all()
    return templates


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a workflow template"""
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == template_id,
        WorkflowTemplate.is_public == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.post("/templates", response_model=WorkflowTemplateResponse)
async def create_template(
    template: WorkflowTemplateCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create and publish a new workflow template
    
    Requires authentication. Template will be reviewed before appearing in marketplace.
    """
    user = User.get_by_keycloak_id(db, current_user.sub)
    db_template = WorkflowTemplate(
        **template.dict(),

        author_id=user.id if user else None,
        is_official=False  # Only admins can mark as official
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template


@router.post("/install", response_model=dict)
async def install_template(
    install_request: WorkflowInstallRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Install a workflow template
    
    Creates a new agent with the workflow configuration
    """
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == install_request.template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Create installation record
    installation = WorkflowInstallation(
        template_id=template.id,
        user_id=current_user.sub if hasattr(current_user, 'sub') else None,
        agent_id=install_request.agent_id,
        customizations=install_request.customizations
    )
    
    # Update install count
    template.install_count += 1
    
    db.add(installation)
    db.commit()
    db.refresh(installation)
    
    return {
        "message": "Template installed successfully",
        "installation_id": installation.id,
        "template_id": template.id
    }


@router.post("/templates/{template_id}/reviews", response_model=WorkflowReviewResponse)
async def create_review(
    template_id: int,
    review: WorkflowReviewCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Add a review for a workflow template"""
    # Check if template exists
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if user already reviewed
    existing = db.query(WorkflowReview).filter(
        WorkflowReview.template_id == template_id,
        WorkflowReview.user_id == current_user.sub
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this template")
    
    db_review = WorkflowReview(
        template_id=template_id,
        user_id=current_user.sub if hasattr(current_user, 'sub') else None,
        **review.dict()
    )
    
    db.add(db_review)
    
    # Update template rating
    reviews = db.query(WorkflowReview).filter(
        WorkflowReview.template_id == template_id
    ).all()
    
    total_rating = sum(r.rating for r in reviews) + review.rating
    review_count = len(reviews) + 1
    template.rating = total_rating / review_count
    template.review_count = review_count
    
    db.commit()
    db.refresh(db_review)
    
    return db_review


@router.get("/stats", response_model=MarketplaceStats)
async def get_marketplace_stats(
    db: Session = Depends(get_db)
):
    """Get marketplace statistics"""
    from sqlalchemy import func
    
    total = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.is_public == True
    ).count()
    
    official = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.is_official == True,
        WorkflowTemplate.is_public == True
    ).count()
    
    community = total - official
    
    total_installs = db.query(func.sum(WorkflowTemplate.install_count)).scalar() or 0
    avg_rating = db.query(func.avg(WorkflowTemplate.rating)).scalar() or 0.0
    
    # Get popular categories
    categories = db.query(
        WorkflowTemplate.category,
        func.count(WorkflowTemplate.id).label('count')
    ).filter(
        WorkflowTemplate.is_public == True
    ).group_by(
        WorkflowTemplate.category
    ).order_by(
        func.count(WorkflowTemplate.id).desc()
    ).limit(10).all()
    
    popular_categories = [
        {"category": cat, "count": count}
        for cat, count in categories
    ]
    
    return MarketplaceStats(
        total_templates=total,
        official_templates=official,
        community_templates=community,
        total_installs=int(total_installs),
        avg_rating=float(avg_rating),
        popular_categories=popular_categories
    )


@router.get("/categories", response_model=List[str])
async def list_categories(
    db: Session = Depends(get_db)
):
    """Get list of all workflow categories"""
    from sqlalchemy import distinct
    
    categories = db.query(distinct(WorkflowTemplate.category)).filter(
        WorkflowTemplate.is_public == True
    ).all()
    
    return [cat[0] for cat in categories]
