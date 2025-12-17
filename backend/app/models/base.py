# from datetime import datetime
# from sqlalchemy import Column, Integer, DateTime
# from sqlalchemy.sql import func
# from sqlalchemy.ext.declarative import declarative_base

# Base = declarative_base()

# class TimestampMixin:
#     created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

# class BaseModel(Base, TimestampMixin):
#     __abstract__ = True
#     id = Column(Integer, primary_key=True, index=True)
    
#     def to_dict(self):
#         return {c.name: getattr(self, c.name) for c in self.__table__.columns}

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

# This should use tenant-aware base from tenancy module
from app.tenancy.context import get_tenant

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

class BaseModel(Base, TimestampMixin):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    
    # CRITICAL: Add schema awareness
    @classmethod
    def __table_args__(cls):
        schema = get_tenant()
        if schema:
            return {'schema': schema}
        return {}
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}