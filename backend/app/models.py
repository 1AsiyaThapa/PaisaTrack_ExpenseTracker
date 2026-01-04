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


# DATABASE TABLES (SQLAlchemy Models)
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID length
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    picture = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(20), nullable=False)
    category = Column(String(100), nullable=False)
    note = Column(String(500), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to user
    user = relationship("User", back_populates="transactions")


# Request/Response Validation Schemas
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
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str
    user: UserResponse


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


# CATEGORY MODELS & SCHEMAS
class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    icon = Column(String(50), nullable=False)  
    color = Column(String(20), nullable=True)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="categories")


User.categories = relationship("Category", back_populates="user")


class CategoryCreate(BaseModel):
    """Schema for creating a category"""
    name: str
    type: Literal["income", "expense"]
    icon: str
    color: Optional[str] = None


class CategoryResponse(BaseModel):
    """Schema for category response"""
    id: str
    name: str
    type: str
    icon: str
    color: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# EMAIL OTP MODEL & SCHEMAS
class EmailOTP(Base):
    __tablename__ = "email_otps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), index=True, nullable=False)
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OTPRequest(BaseModel):
    """Schema for requesting OTP"""
    email: str
    name: str


class OTPVerifyRequest(BaseModel):
    """Schema for verifying OTP during signup"""
    email: str
    name: str
    password: str
    otp_code: str


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = None
    password: Optional[str] = None
    new_password: Optional[str] = None


