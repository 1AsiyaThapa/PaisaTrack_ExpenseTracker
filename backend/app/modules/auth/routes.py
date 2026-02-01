from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import httpx
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from .schemas import (
    TokenResponse,
    LoginRequest,
    SignupRequest,
    OTPRequest,
    OTPVerifyRequest,
)
from .service import AuthService
from .email_service import send_otp_email
from app.modules.users.service import UserService
from app.modules.users.repository import UserRepository

router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)


@router.get("/google")
def google_login():
    google_auth_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{settings.BACKEND_URL}/auth/google/callback",
        "scope": "openid email profile",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"{google_auth_url}?{urlencode(params)}"
    return {"auth_url": auth_url}


@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        auth_service = get_auth_service(db)

        with httpx.Client() as client:
            token_response = client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": f"{settings.BACKEND_URL}/auth/google/callback",
                },
            )

            if token_response.status_code != 200:
                error_url = f"{settings.FRONTEND_URL}/login?error=token_exchange_failed"
                return RedirectResponse(url=error_url)

            tokens = token_response.json()
            access_token = tokens.get("access_token")

            user_response = client.get(
                f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
            )

            if user_response.status_code != 200:
                error_url = f"{settings.FRONTEND_URL}/login?error=user_info_failed"
                return RedirectResponse(url=error_url)

            user_info = user_response.json()

            token_data = auth_service.authenticate_with_google(user_info)

            redirect_url = f"{settings.FRONTEND_URL}/dashboard"

            response = RedirectResponse(url=redirect_url)
            response.set_cookie(
                key="auth_token",
                value=token_data.access_token,
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                httponly=True,
                secure=False,
                samesite="lax",
            )
            return response

    except Exception:
        error_url = f"{settings.FRONTEND_URL}/login?error=auth_failed"
        return RedirectResponse(url=error_url)


@router.post("/google/token", response_model=TokenResponse)
def google_token_auth(
    google_token: str, auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate with Google token (for frontend use)"""
    user_info = auth_service.verify_google_token(google_token)
    return auth_service.authenticate_with_google(user_info)


@router.post("/request-otp")
def request_otp(
    otp_request: OTPRequest,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Request OTP for email verification before signup"""
    existing_user = user_service.get_user_by_email(otp_request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    otp_code = auth_service.create_otp(otp_request.email)

    email_sent = send_otp_email(
        to_email=otp_request.email, otp_code=otp_code, name=otp_request.name
    )

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email. Please try again.",
        )

    return {"message": "OTP sent to your email", "email": otp_request.email}


@router.post("/signup", response_model=TokenResponse)
def signup_with_email(
    signup_data: OTPVerifyRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Sign up with email and password after OTP verification"""
    auth_service.verify_otp(signup_data.email, signup_data.otp_code)

    signup_request = SignupRequest(
        email=signup_data.email, name=signup_data.name, password=signup_data.password
    )

    token_data = auth_service.signup_with_email(signup_request)

    response.set_cookie(
        key="auth_token",
        value=token_data.access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return token_data


@router.post("/login", response_model=TokenResponse)
def login_with_email(
    login_data: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login with email and password"""
    token_data = auth_service.login_with_email(login_data)

    if login_data.remember_me:
        cookie_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    else:
        cookie_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    response.set_cookie(
        key="auth_token",
        value=token_data.access_token,
        max_age=cookie_max_age,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return token_data


@router.post("/logout")
def logout(response: Response):
    """Logout endpoint (clear cookie)"""
    response.delete_cookie(key="auth_token")
    return {"message": "Logged out successfully"}


@router.get("/status")
def auth_status(
    request: Request, user_service: UserService = Depends(get_user_service)
):
    """Check authentication status without throwing 401"""
    token = request.cookies.get("auth_token")
    if not token:
        return {"authenticated": False, "user": None}

    try:
        from app.core.security import decode_token

        user_id = decode_token(token)

        if user_id:
            user = user_service.get_user_by_id(user_id)
            if user:
                return {
                    "authenticated": True,
                    "user": user_service.get_user_response(user),
                }

        return {"authenticated": False, "user": None}
    except Exception:
        return {"authenticated": False, "user": None}
