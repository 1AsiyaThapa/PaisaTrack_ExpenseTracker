import uuid
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_google_token as verify_google_token_func,
)
from app.core.config import settings
from .repository import AuthRepository
from .schemas import SignupRequest, LoginRequest, TokenResponse
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService
from app.modules.users.models import User


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.auth_repo = AuthRepository(db)
        self.user_repo = UserRepository(db)
        self.user_service = UserService(self.user_repo)

    def verify_google_token(self, token: str) -> dict:
        """Verify Google access token and get user info"""
        return verify_google_token_func(token)

    def authenticate_with_google(self, google_user: dict) -> TokenResponse:
        """Authenticate user with Google info"""
        existing_user = self.user_service.get_user_by_google_id(google_user["id"])

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
            user = self.user_service.create_user(user)

        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=self.user_service.get_user_response(user),
        )

    def signup_with_email(self, signup_data: SignupRequest) -> TokenResponse:
        """Sign up a new user with email/password"""
        existing_user = self.user_service.get_user_by_email(signup_data.email)
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
        user = self.user_service.create_user(user)

        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=self.user_service.get_user_response(user),
        )

    def login_with_email(self, login_data: LoginRequest) -> TokenResponse:
        """Login user with email/password"""
        user = self.user_service.get_user_by_email(login_data.email)

        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if login_data.remember_me:
            expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        else:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=expires_delta,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=self.user_service.get_user_response(user),
        )

    def create_otp(self, email: str) -> str:
        """Create and store an OTP for email verification"""
        return self.auth_repo.create_otp(email)

    def verify_otp(self, email: str, otp_code: str) -> bool:
        """Verify OTP code"""
        return self.auth_repo.verify_otp(email, otp_code)
