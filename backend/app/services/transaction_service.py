"""
Transaction service functions for PaisaTrack
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionCreate, TransactionResponse


# ============================================================
# TRANSACTION SERVICE FUNCTIONS
# ============================================================
def create_transaction(db: Session, user_id: str, data: TransactionCreate) -> Transaction:
    """Create a new transaction for a user"""
    transaction = Transaction(
        user_id=user_id,
        amount=data.amount,
        type=data.type,
        category=data.category,
        note=data.note,
        date=data.date,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def get_user_transactions(db: Session, user_id: str) -> List[Transaction]:
    """Get all transactions for a specific user"""
    return db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.date.desc()).all()


def get_transaction_by_id(db: Session, transaction_id: str) -> Optional[Transaction]:
    """Get a transaction by its ID"""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def delete_transaction(db: Session, transaction_id: str) -> bool:
    """Delete a transaction by ID"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if transaction:
        db.delete(transaction)
        db.commit()
        return True
    return False


def get_transaction_response(transaction: Transaction) -> TransactionResponse:
    """Convert Transaction model to TransactionResponse"""
    return TransactionResponse(
        id=transaction.id,
        amount=transaction.amount,
        type=transaction.type,
        category=transaction.category,
        note=transaction.note,
        date=transaction.date,
        created_at=transaction.created_at,
    )

