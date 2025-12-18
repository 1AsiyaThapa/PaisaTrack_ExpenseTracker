"""
Transaction routes for PaisaTrack
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.models import get_db, Transaction, TransactionCreate, TransactionResponse
from app.services import transaction_service, auth_service

router = APIRouter()


def get_current_user_id(request: Request) -> str:
    """
    Simple helper to get current user ID from JWT token in cookie.
    """
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token found",
        )

    payload = auth_service.verify_token(token)
    return payload.get("sub")


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new transaction for the authenticated user"""
    user_id = get_current_user_id(request)
    
    transaction = transaction_service.create_transaction(db, user_id, data)
    return transaction_service.get_transaction_response(transaction)


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    request: Request,
    db: Session = Depends(get_db),
    type: Optional[str] = Query(None, description="Filter by transaction type: 'income' or 'expense'"),
):
    """Get all transactions for the authenticated user, optionally filtered by type"""
    user_id = get_current_user_id(request)
    
    transactions = transaction_service.get_user_transactions(db, user_id, type)
    return [transaction_service.get_transaction_response(t) for t in transactions]


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a transaction by ID (only if it belongs to the authenticated user)"""
    user_id = get_current_user_id(request)
    
    # First, verify the transaction exists and belongs to the user
    transaction = transaction_service.get_transaction_by_id(db, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    if transaction.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this transaction",
        )
    
    transaction_service.delete_transaction(db, transaction_id)
    return None


@router.get("/stats")
async def get_dashboard_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get dashboard statistics for the authenticated user"""
    user_id = get_current_user_id(request)
    return transaction_service.get_user_stats(db, user_id)
