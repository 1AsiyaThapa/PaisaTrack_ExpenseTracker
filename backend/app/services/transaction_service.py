from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.models import Transaction, TransactionCreate, TransactionResponse


# TRANSACTION SERVICE FUNCTIONS
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


def get_user_transactions(db: Session, user_id: str, type: Optional[str] = None) -> List[Transaction]:
    """Get all transactions for a specific user, optionally filtered by type"""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if type:
        query = query.filter(Transaction.type == type)
    return query.order_by(Transaction.date.desc()).all()


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


def get_user_stats(db: Session, user_id: str) -> dict:
    """Get dashboard statistics for a user"""
    # Total income
    total_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "income"
    ).scalar() or Decimal("0")
    
    # Total expenses
    total_expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense"
    ).scalar() or Decimal("0")
    
    # Balance
    balance = total_income - total_expenses
    
    # Recent transactions (last 5)
    recent = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(Transaction.date.desc()).limit(5).all()
    
    return {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "balance": float(balance),
        "recent_transactions": [get_transaction_response(t) for t in recent]
    }

