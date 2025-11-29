"""
Transaction routes for PaisaTrack (placeholder)
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_transactions():
    """Get user transactions (placeholder)"""
    return {"message": "Transactions endpoint - to be implemented"}


@router.post("/")
async def create_transaction():
    """Create a new transaction (placeholder)"""
    return {"message": "Create transaction endpoint - to be implemented"}