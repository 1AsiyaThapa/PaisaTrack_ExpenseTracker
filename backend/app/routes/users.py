"""
User routes for PaisaTrack
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.models import get_db, UserResponse
from app.services import user_service, auth_service

router = APIRouter()


def get_current_user_id(request: Request) -> str:
    """
    Simple helper to get current user ID from JWT token in cookie.
    This replaces the complex Dependency Injection approach.
    """
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token found",
        )

    payload = auth_service.verify_token(token)
    return payload.get("sub")


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated user"""
    user_id = get_current_user_id(request)
    
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )

    return user_service.get_user_response(user)
