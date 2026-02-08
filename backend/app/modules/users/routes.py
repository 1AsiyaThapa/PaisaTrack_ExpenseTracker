from fastapi import APIRouter, HTTPException, status

from app.core.database import DBSession
from app.core.security import CurrentUserID, hash_password, verify_password

from .models import User
from .schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: DBSession,
    user_id: CurrentUserID,
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    db: DBSession,
    user_id: CurrentUserID,
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data and "new_password" in update_data:
        if not user.password_hash or not verify_password(
            update_data["password"], user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password",
            )
        user.password_hash = hash_password(update_data["new_password"])

    # Remove fields that shouldn't be directly set on the model or have been handled
    update_data.pop("password", None)
    update_data.pop("new_password", None)

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return user
