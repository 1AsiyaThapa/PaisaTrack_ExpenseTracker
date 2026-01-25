from typing import Optional
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import UserResponse


# USER SERVICE FUNCTIONS
def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
    """Get user by Google ID"""
    return db.query(User).filter(User.google_id == google_id).first()


def create_user(db: Session, user: User) -> User:
    """Create a new user"""
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: str, **updates) -> Optional[User]:
    """Update user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in updates.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user


def delete_user(db: Session, user_id: str) -> bool:
    """Delete user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


def get_user_response(user: User) -> UserResponse:
    """Convert User model to UserResponse"""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        google_id=user.google_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
