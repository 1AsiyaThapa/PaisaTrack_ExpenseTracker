import os
from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import httpx
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.models import get_db
from app.schemas import TokenResponse, LoginRequest, SignupRequest, OTPRequest, OTPVerifyRequest
from app.services import auth_service, user_service, otp_service, email_service

# Load config from .env
load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

router = APIRouter()


@router.get("/google")
async def google_login():
    google_auth_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BACKEND_URL}/auth/google/callback",
        "scope": "openid email profile",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"{google_auth_url}?{urlencode(params)}"
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": f"{BACKEND_URL}/auth/google/callback",
                },
            )

            if token_response.status_code != 200:
                error_url = f"{FRONTEND_URL}/login?error=token_exchange_failed"
                return RedirectResponse(url=error_url)

            tokens = token_response.json()
            access_token = tokens.get("access_token")

            # Get user info from Google (using simple dict, not Pydantic)
            user_response = await client.get(
                f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
            )

            if user_response.status_code != 200:
                error_url = f"{FRONTEND_URL}/login?error=user_info_failed"
                return RedirectResponse(url=error_url)

            # Just use the dictionary directly
            user_info = user_response.json()

            # Authenticate user
            token_data = auth_service.authenticate_with_google(db, user_info)

            # Create redirect response with cookie
            redirect_url = f"{FRONTEND_URL}/dashboard"

            response = RedirectResponse(url=redirect_url)
            response.set_cookie(
                key="auth_token",
                value=token_data.access_token,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                httponly=True,
                secure=False,
                samesite="lax",
            )
            return response

    except Exception:
        # Redirect to frontend with error
        error_url = f"{FRONTEND_URL}/login?error=auth_failed"
        return RedirectResponse(url=error_url)


@router.post("/google/token", response_model=TokenResponse)
async def google_token_auth(google_token: str, db: Session = Depends(get_db)):
    """Authenticate with Google token (for frontend use)"""
    user_info = await auth_service.verify_google_token(google_token)
    return auth_service.authenticate_with_google(db, user_info)


@router.post("/request-otp")
async def request_otp(otp_request: OTPRequest, db: Session = Depends(get_db)):
    """Request OTP for email verification before signup"""
    # Check if user already exists
    existing_user = user_service.get_user_by_email(db, otp_request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Generate and store OTP
    otp_code = otp_service.create_otp(db, otp_request.email)
    
    # Send OTP via email
    email_sent = email_service.send_otp_email(
        to_email=otp_request.email,
        otp_code=otp_code,
        name=otp_request.name
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email. Please try again.",
        )
    
    return {"message": "OTP sent to your email", "email": otp_request.email}


@router.post("/signup", response_model=TokenResponse)
async def signup_with_email(signup_data: OTPVerifyRequest, response: Response, db: Session = Depends(get_db)):
    """Sign up with email and password after OTP verification"""
    # Verify OTP first
    otp_service.verify_otp(db, signup_data.email, signup_data.otp_code)
    
    # Create signup request object
    signup_request = SignupRequest(
        email=signup_data.email,
        name=signup_data.name,
        password=signup_data.password
    )
    
    # Create user account
    token_data = auth_service.signup_with_email(db, signup_request)

    # Set cookie
    response.set_cookie(
        key="auth_token",
        value=token_data.access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return token_data


@router.post("/login", response_model=TokenResponse)
async def login_with_email(login_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Login with email and password"""
    token_data = auth_service.login_with_email(db, login_data)

    # Set cookie with appropriate expiration
    if login_data.remember_me:
        cookie_max_age = 30 * 24 * 60 * 60  # 30 days in seconds
    else:
        cookie_max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60

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
async def logout(response: Response):
    """Logout endpoint (clear cookie)"""
    response.delete_cookie(key="auth_token")
    return {"message": "Logged out successfully"}


@router.get("/status")
async def auth_status(request: Request, db: Session = Depends(get_db)):
    """Check authentication status without throwing 401"""
    token = request.cookies.get("auth_token")
    if not token:
        return {"authenticated": False, "user": None}

    try:
        payload = auth_service.verify_token(token)
        user_id = payload.get("sub")

        if user_id:
            user = user_service.get_user_by_id(db, user_id)
            if user:
                return {
                    "authenticated": True,
                    "user": user_service.get_user_response(user)
                }

        return {"authenticated": False, "user": None}
    except Exception:
        return {"authenticated": False, "user": None}