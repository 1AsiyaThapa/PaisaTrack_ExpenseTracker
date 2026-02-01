from typing import Optional
from .repository import UserRepository
from .models import User
from .schemas import UserResponse


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.repo.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.repo.get_by_email(email)

    def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        return self.repo.get_by_google_id(google_id)

    def create_user(self, user: User) -> User:
        """Create a new user"""
        return self.repo.create(user)

    def update_user(self, user_id: str, **updates) -> Optional[User]:
        """Update user by ID"""
        return self.repo.update(user_id, **updates)

    def delete_user(self, user_id: str) -> bool:
        """Delete user by ID"""
        return self.repo.delete(user_id)

    def get_user_response(self, user: User) -> UserResponse:
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
