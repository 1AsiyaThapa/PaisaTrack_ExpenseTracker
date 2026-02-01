from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from .models import Category
from .schemas import CategoryCreate


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(self, user_id: str, type: Optional[str] = None) -> List[Category]:
        stmt = select(Category).where(Category.user_id == user_id)
        if type:
            stmt = stmt.where(Category.type == type)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, category_id: str, user_id: str) -> Optional[Category]:
        stmt = select(Category).where(
            Category.id == category_id, Category.user_id == user_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name_and_type(
        self, user_id: str, name: str, type: str
    ) -> Optional[Category]:
        stmt = select(Category).where(
            Category.user_id == user_id,
            Category.name == name,
            Category.type == type,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user_id: str, data: CategoryCreate) -> Category:
        category = Category(user_id=user_id, **data.model_dump())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(
        self, category_id: str, user_id: str, data: CategoryCreate
    ) -> Optional[Category]:
        category = self.get_by_id(category_id, user_id)
        if category:
            for key, value in data.model_dump().items():
                setattr(category, key, value)
            self.db.commit()
            self.db.refresh(category)
        return category

    def delete(self, category_id: str, user_id: str) -> bool:
        stmt = delete(Category).where(
            Category.id == category_id, Category.user_id == user_id
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
