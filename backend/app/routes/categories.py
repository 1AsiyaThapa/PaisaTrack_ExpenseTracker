from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.models import get_db, Category
from app.schemas import CategoryCreate, CategoryResponse
from app.services import auth_service

router = APIRouter()


def get_current_user_id(request: Request) -> str:
    # Helper to get current user ID from JWT token in cookie.
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token found",
        )

    payload = auth_service.verify_token(token)
    return payload.get("sub")


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(request: Request, type: str = None, db: Session = Depends(get_db)):
    """Get all categories for the current user, optionally filtered by type"""
    user_id = get_current_user_id(request)
    
    query = db.query(Category).filter(Category.user_id == user_id)
    if type:
        query = query.filter(Category.type == type)
        
    return query.all()


@router.post("/", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, request: Request, db: Session = Depends(get_db)):
    """Create a new category"""
    user_id = get_current_user_id(request)
    
    # Check if category with same name exists for user
    existing = db.query(Category).filter(
        Category.user_id == user_id,
        Category.name == category.name,
        Category.type == category.type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category.name}' already exists for {category.type}"
        )
    
    new_category = Category(
        user_id=user_id,
        name=category.name,
        type=category.type,
        icon=category.icon,
        color=category.color
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, category_update: CategoryCreate, request: Request, db: Session = Depends(get_db)):
    """Update a category"""
    user_id = get_current_user_id(request)
    
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
        
    category.name = category_update.name
    category.type = category_update.type
    category.icon = category_update.icon
    category.color = category_update.color
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{category_id}")
async def delete_category(category_id: str, request: Request, db: Session = Depends(get_db)):
    """Delete a category"""
    user_id = get_current_user_id(request)
    
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
        
    db.delete(category)
    db.commit()
    
    return {"message": "Category deleted successfully"}
