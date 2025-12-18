from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)  # Up to 12 digits, 2 decimal places
    type = Column(String(20), nullable=False)  # "income" or "expense"
    category = Column(String(100), nullable=False)  # e.g., "food", "salary"
    note = Column(String(500), nullable=True)  # Optional description
    date = Column(DateTime(timezone=True), nullable=False)  # When transaction happened
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to user
    user = relationship("User", back_populates="transactions")


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


class LoginRequest(BaseModel):
    """Schema for email/password login"""
    email: str
    password: str
    remember_me: bool = False


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


# ============================================================
# 4. TRANSACTION SCHEMAS
# ============================================================
class TransactionCreate(BaseModel):
    """Schema for creating a new transaction"""
    amount: Decimal
    type: Literal["income", "expense"]
    category: str
    note: Optional[str] = None
    date: datetime


class TransactionResponse(BaseModel):
    """Schema for transaction response"""
    id: str
    amount: Decimal
    type: str
    category: str
    note: Optional[str] = None
    date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

