"""
Budget routes for PaisaTrack (placeholder)
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_budgets():
    """Get user budgets (placeholder)"""
    return {"message": "Budgets endpoint - to be implemented"}


@router.post("/")
async def create_budget():
    """Create a new budget (placeholder)"""
    return {"message": "Create budget endpoint - to be implemented"}