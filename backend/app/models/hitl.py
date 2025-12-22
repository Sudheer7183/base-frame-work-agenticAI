"""Human-in-the-Loop (HITL) models"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class HITLRecord(Base):
    """
    Human-in-the-Loop record
    Stores items requiring human review/approval
    """
    __tablename__ = "hitl_records"
    id = Column(Integer, primary_key=True, index=True)
    # Core fields
    agent_id = Column(Integer, ForeignKey('agents.id', ondelete='CASCADE'), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False, index=True)
    execution_id = Column(String(255), nullable=True, index=True)
    
    # Data
    input_data = Column(JSON, nullable=False, default={})
    output_data = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(String(50), nullable=False, default='pending', index=True)
    priority = Column(String(20), nullable=False, default='normal', index=True)
    
    # Feedback
    feedback = Column(JSON, nullable=True)
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    reviewed_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Escalation
    timeout_at = Column(DateTime(timezone=True), nullable=True)
    escalated = Column(Boolean, nullable=False, default=False, index=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    agent = relationship("AgentConfig", back_populates="hitl_records")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "execution_id": self.execution_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status,
            "priority": self.priority,
            "feedback": self.feedback,
            "assigned_to": self.assigned_to,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "timeout_at": self.timeout_at.isoformat() if self.timeout_at else None,
            "escalated": self.escalated,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_pending(cls, db):
        """Get all pending HITL records"""
        return db.query(cls).filter(cls.status == 'pending').all()
    
    @classmethod
    def get_by_agent(cls, db, agent_id):
        """Get HITL records for specific agent"""
        return db.query(cls).filter(cls.agent_id == agent_id).all()
    
    def __repr__(self):
        return f"<HITLRecord(id={self.id}, agent='{self.agent_name}', status='{self.status}')>"
