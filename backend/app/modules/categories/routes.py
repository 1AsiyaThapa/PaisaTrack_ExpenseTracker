from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user_id
from .schemas import CategoryCreate, CategoryResponse
from .repository import CategoryRepository
from .service import CategoryService

router = APIRouter()


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    repo = CategoryRepository(db)
    return CategoryService(repo)


@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    type: str = None,
    user_id: str = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
):
    categories = service.get_user_categories(user_id, type)
    return categories


@router.post("/", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    user_id: str = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
):
    new_category = service.create_category(user_id, category)
    return new_category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    category_update: CategoryCreate,
    user_id: str = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
):
    category = service.update_category(category_id, user_id, category_update)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CategoryService = Depends(get_category_service),
):
    deleted = service.delete_category(category_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    return {"message": "Category deleted successfully"}
