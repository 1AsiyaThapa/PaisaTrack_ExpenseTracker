from typing import Optional, List
from .repository import CategoryRepository
from .models import Category
from .schemas import CategoryCreate


class CategoryService:
    def __init__(self, repo: CategoryRepository):
        self.repo = repo

    def get_user_categories(
        self, user_id: str, type: Optional[str] = None
    ) -> List[Category]:
        """Get all categories for a user, optionally filtered by type"""
        return self.repo.get_by_user(user_id, type)

    def get_category_by_id(self, category_id: str, user_id: str) -> Optional[Category]:
        """Get a category by ID"""
        return self.repo.get_by_id(category_id, user_id)

    def create_category(self, user_id: str, data: CategoryCreate) -> Category:
        """Create a new category"""
        # Check if category with same name exists for user
        existing = self.repo.get_by_name_and_type(user_id, data.name, data.type)
        if existing:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{data.name}' already exists for {data.type}",
            )
        return self.repo.create(user_id, data)

    def update_category(
        self, category_id: str, user_id: str, data: CategoryCreate
    ) -> Optional[Category]:
        """Update a category"""
        return self.repo.update(category_id, user_id, data)

    def delete_category(self, category_id: str, user_id: str) -> bool:
        """Delete a category"""
        return self.repo.delete(category_id, user_id)
