import enum
import uuid

from sqlalchemy import Column, String, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UserRole(str, enum.Enum):
    WORKER = "worker"
    SUPERVISOR = "supervisor"
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    language_pref = Column(String, nullable=False, default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
