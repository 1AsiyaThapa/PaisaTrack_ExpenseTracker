from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from decimal import Decimal
from datetime import datetime

from app.models import Transaction
from app.schemas import TransactionCreate, TransactionResponse, IncomeExpenseDataPoint


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


def get_income_expense_comparison(db: Session, user_id: str, months: int = 6) -> list[IncomeExpenseDataPoint]:
    """Get monthly income vs expense comparison data"""
    income_data = db.query(
        extract('year', Transaction.date).label('year'),
        extract('month', Transaction.date).label('month'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == user_id,
        Transaction.type == "income"
    ).group_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).order_by(
        extract('year', Transaction.date).desc(),
        extract('month', Transaction.date).desc()
    ).limit(months).all()
    
    expense_data = db.query(
        extract('year', Transaction.date).label('year'),
        extract('month', Transaction.date).label('month'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense"
    ).group_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).order_by(
        extract('year', Transaction.date).desc(),
        extract('month', Transaction.date).desc()
    ).limit(months).all()
    
    income_dict = {(int(row.year), int(row.month)): float(row.total) for row in income_data}
    expense_dict = {(int(row.year), int(row.month)): float(row.total) for row in expense_data}
    
    all_months = sorted(set(list(income_dict.keys()) + list(expense_dict.keys())), reverse=True)[:months]
    all_months.reverse()
    
    result = []
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for year, month in all_months:
        month_label = f"{month_names[month - 1]} {year}"
        result.append(IncomeExpenseDataPoint(
            month=month_label,
            income=income_dict.get((year, month), 0.0),
            expense=expense_dict.get((year, month), 0.0)
        ))
    
    return result

