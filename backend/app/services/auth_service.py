import httpx
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.models import User, SignupRequest, LoginRequest, TokenResponse, UserResponse
from app.services import user_service

# ============================================================
# CONFIG - Load from .env
# ============================================================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def hash_password(password: str) -> str:
    """Hash password using SHA256 + secret key"""
    return hashlib.sha256(f"{password}{SECRET_KEY}".encode()).hexdigest()


# ============================================================
# AUTH FUNCTIONS
# ============================================================
async def verify_google_token(token: str) -> dict:
    """Verify Google access token and get user info"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={token}"
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token",
                )

            return response.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify Google token",
        )


def authenticate_with_google(db: Session, google_user: dict) -> TokenResponse:
    """Authenticate user with Google info"""
    existing_user = user_service.get_user_by_google_id(db, google_user["id"])

    if existing_user:
        user = existing_user
    else:
        user = User(
            id=str(uuid.uuid4()),
            google_id=google_user["id"],
            email=google_user["email"],
            name=google_user["name"],
            picture=google_user.get("picture"),
        )
        user = user_service.create_user(db, user)

    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_service.get_user_response(user),
    )


def signup_with_email(db: Session, signup_data: SignupRequest) -> TokenResponse:
    """Sign up a new user with email/password"""
    existing_user = user_service.get_user_by_email(db, signup_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = User(
        id=str(uuid.uuid4()),
        email=signup_data.email,
        name=signup_data.name,
        picture=signup_data.picture,
        password_hash=hash_password(signup_data.password),
    )
    user = user_service.create_user(db, user)

    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_service.get_user_response(user),
    )