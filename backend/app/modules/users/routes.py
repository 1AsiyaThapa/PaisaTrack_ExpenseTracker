from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id, verify_password, hash_password
from .schemas import UserResponse, UserUpdate
from .service import UserService
from .repository import UserRepository

router = APIRouter()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)


@router.get("/me", response_model=UserResponse)
def get_current_user(
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user_service.get_user_response(user)


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    updates = {}
    if user_update.name:
        updates["name"] = user_update.name

    if user_update.password and user_update.new_password:
        if not verify_password(user_update.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password",
            )
        updates["password_hash"] = hash_password(user_update.new_password)

    if updates:
        updated_user = user_service.update_user(user_id, **updates)
        return user_service.get_user_response(updated_user)

    return user_service.get_user_response(user)
