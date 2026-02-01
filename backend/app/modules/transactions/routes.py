from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id
from .schemas import (
    TransactionCreate,
    TransactionResponse,
    IncomeExpenseComparisonResponse,
)
from .repository import TransactionRepository
from .service import TransactionService

router = APIRouter()


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    repo = TransactionRepository(db)
    return TransactionService(repo, db)


@router.post(
    "/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
def create_transaction(
    data: TransactionCreate,
    user_id: str = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
):
    transaction = service.create_user_transaction(user_id, data)
    return service.get_transaction_response(transaction)


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    type: Optional[str] = Query(
        None, description="Filter by transaction type: 'income' or 'expense'"
    ),
    user_id: str = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
):
    transactions = service.get_user_transactions(user_id, type)
    return [service.get_transaction_response(t) for t in transactions]


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
):
    transaction = service.get_transaction_by_id(transaction_id)
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

    service.delete_transaction(transaction_id)
    return None


@router.get("/stats")
def get_dashboard_stats(
    user_id: str = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
):
    return service.get_user_stats(user_id)


@router.get(
    "/income-expense-comparison", response_model=IncomeExpenseComparisonResponse
)
def get_income_expense_comparison(
    months: int = Query(
        6, ge=1, le=12, description="Number of months to retrieve (1-12)"
    ),
    user_id: str = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
):
    data = service.get_income_expense_comparison(user_id, months)
    return IncomeExpenseComparisonResponse(data=data)


@router.get("/dashboard-summary")
def get_dashboard_summary(
    months: int = Query(
        6, ge=1, le=12, description="Number of months to retrieve (1-12)"
    ),
    user_id: str = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
):
    """Get detailed summary for dashboard: stacked expenses by category + income line"""
    data = service.get_dashboard_summary(user_id, months)
    return {"data": data}


@router.get("/category-proportions")
def get_category_proportions(
    type: str = Query(..., description="Transaction type: 'income' or 'expense'"),
    user_id: str = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
):
    """Get category proportions for income or expense"""
    if type not in ["income", "expense"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type must be 'income' or 'expense'",
        )
    data = service.get_category_proportions(user_id, type)
    return {"data": data}


@router.post("/scan")
def scan_receipt(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
):
    """Scan receipt image using AI and return extracted data"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image"
        )

    file_url = service.save_receipt_file(file)

    file.file.seek(0)
    file_bytes = file.file.read()

    try:
        analysis = service.scan_receipt(user_id, file_bytes, file.content_type)
        return {"receipt_url": file_url, "analysis": analysis.model_dump()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan receipt: {str(e)}",
        )
