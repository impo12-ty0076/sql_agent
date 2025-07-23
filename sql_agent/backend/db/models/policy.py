"""
SQLAlchemy models for policy management
"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

from ..session import Base


class Policy(Base):
    """Policy database model"""
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    policy_type = Column(Enum("user_permission", "query_limit", "security", name="policy_type"), nullable=False)
    status = Column(Enum("active", "inactive", "draft", name="policy_status"), nullable=False, default="draft")
    applies_to_roles = Column(JSON, nullable=False, default=lambda: ["user"])
    priority = Column(Integer, nullable=False, default=0)
    settings = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_policies")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type,
            "status": self.status,
            "applies_to_roles": self.applies_to_roles,
            "priority": self.priority,
            "settings": self.settings,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by
        }