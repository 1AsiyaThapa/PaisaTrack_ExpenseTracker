from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv

# ============================================================
# 1. DATABASE SETUP & CONFIG (MySQL)
# ============================================================
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# 2. DATABASE TABLES (SQLAlchemy Models)
# ============================================================
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID length
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    picture = Column(String(512), nullable=True)  # URLs can be long
    role = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================================
# 3. PYDANTIC SCHEMAS (Request/Response Validation)
# ============================================================
class UserBase(BaseModel):
    """Base user schema"""
    email: str
    name: str
    picture: Optional[str] = None


class SignupRequest(UserBase):
    """Schema for email/password signup"""
    password: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    google_id: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Important for ORM mode


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str
    user: UserResponse

