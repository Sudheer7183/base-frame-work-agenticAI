"""Agent models for the Agentic AI Platform"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from .base import Base


class AgentConfig(Base):
    """
    Agent configuration model
    Stores agent metadata and configuration
    """
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    # Core fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    workflow = Column(String(255), nullable=False, index=True)
    config = Column(JSON, nullable=False, default={})
    active = Column(Boolean, nullable=False, default=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    
    # Relationships
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    creator = relationship("User", back_populates="agents")
    
    # Execution logs
    execution_logs = relationship("AgentExecutionLog", back_populates="agent", cascade="all, delete-orphan")
    
    # HITL records
    hitl_records = relationship("HITLRecord", back_populates="agent", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "workflow": self.workflow,
            "config": self.config,
            "active": self.active,
            "version": self.version,
            "created_by": self.created_by,
            # "created_at": self.created_at.isoformat() if self.created_at else None,
            # "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<AgentConfig(id={self.id}, name='{self.name}', active={self.active})>"


class AgentExecutionLog(Base):
    """
    Agent execution log for audit trail
    Tracks all agent executions
    """
    __tablename__ = "agent_execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id', ondelete='CASCADE'), nullable=False, index=True)
    execution_id = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, index=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    started_by =  Column(String(255), nullable=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    agent = relationship("AgentConfig", back_populates="execution_logs")
    # user = relationship("User")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "started_by": self.started_by,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
