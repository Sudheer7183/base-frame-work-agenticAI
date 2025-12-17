from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base

class UserTenant(Base):
    __tablename__ = "user_tenants"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"))

    role = Column(String, default="member")  # admin, member, viewer

    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant"),
    )
