import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

from anyio.to_thread import run_sync
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, UploadFile, status
from google import genai
from google.genai import types
from sqlalchemy import CursorResult, delete, desc, extract, func, select

from app.core.config import settings
from app.core.constants import DEFAULT_CATEGORY
from app.core.database import DBSession
from app.core.security import CurrentUserID
from app.modules.categories.models import Category
from app.modules.budgets.models import Budget
from app.modules.auth.email_service import send_budget_alert

from .helpers import process_dashboard_summary
from .models import Transaction, TransactionType
from .schemas import (
    IncomeExpenseComparisonResponse,
    IncomeExpenseDataPoint,
    MultiReceiptAnalysis,
    TransactionCreate,
    TransactionResponse,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


async def check_budget_notifications(
    user_id: str,
    db: DBSession,
    user_email: str,
    user_name: str,
):
    """Background task to check budget threshold and send notifications"""
    now = datetime.now()
    
    # 1. Get Budget for current month
    b_stmt = select(Budget).where(
        Budget.user_id == user_id,
        Budget.month == now.month,
        Budget.year == now.year
    )
    budget = (await db.execute(b_stmt)).scalar_one_or_none()
    
    if not budget or budget.amount <= 0 or budget.notified_80:
        return
    
    # 2. Get Spent this month
    s_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        extract('month', Transaction.date) == now.month,
        extract('year', Transaction.date) == now.year
    )
    spent = (await db.execute(s_stmt)).scalar() or 0
    
    # 3. Check threshold
    if float(spent) >= (float(budget.amount) * 0.8):
        await send_budget_alert(user_email, user_name, 80)
        budget.notified_80 = True
        await db.commit()


@router.post(
    "/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    data: TransactionCreate,
    db: DBSession,
    user_id: CurrentUserID,
    background_tasks: BackgroundTasks,
):
    transaction = Transaction(user_id=user_id, **data.model_dump())
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    # Trigger budget check in background for expense transactions
    if data.type == TransactionType.EXPENSE:
        # Get user info for notification
        from app.modules.users.models import User
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if user:
            background_tasks.add_task(
                check_budget_notifications,
                user_id,
                db,
                user.email,
                user.name
            )
    
    return transaction


@router.get("/", response_model=list[TransactionResponse])
async def get_transactions(
    db: DBSession,
    user_id: CurrentUserID,
    type: TransactionType | None = Query(
        None, description="Filter by transaction type"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    stmt = select(Transaction).where(Transaction.user_id == user_id)
    if type:
        stmt = stmt.where(Transaction.type == type)
    stmt = stmt.order_by(Transaction.date.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    db: DBSession,
    user_id: CurrentUserID,
):
    stmt = delete(Transaction).where(
        Transaction.id == transaction_id, Transaction.user_id == user_id
    )
    result = cast(CursorResult, await db.execute(stmt))
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return None


@router.get("/stats")
async def get_dashboard_stats(
    db: DBSession,
    user_id: CurrentUserID,
    days: int = Query(None, description="Filter by last N days (7, 30, or 90)"),
):
    now = datetime.now()
    
    # Build date filter if days parameter is provided
    date_filter = []
    if days:
        start_date = now - timedelta(days=days)
        date_filter = [Transaction.date >= start_date]
    
    # Total Income (filtered by days if provided)
    income_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.INCOME,
        *date_filter
    )
    # Total Expense (filtered by days if provided)
    expense_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        *date_filter
    )

    total_income_res = await db.execute(income_stmt)
    total_expense_res = await db.execute(expense_stmt)

    total_income = total_income_res.scalar() or Decimal("0")
    total_expense = total_expense_res.scalar() or Decimal("0")

    # Monthly Specific Expense for Budget Calculation (always current month)
    monthly_expense_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        extract('month', Transaction.date) == now.month,
        extract('year', Transaction.date) == now.year
    )
    monthly_spent = (await db.execute(monthly_expense_stmt)).scalar() or 0

    # Get Current Budget
    budget_stmt = select(Budget).where(
        Budget.user_id == user_id,
        Budget.month == now.month,
        Budget.year == now.year
    )
    budget_res = await db.execute(budget_stmt)
    budget = budget_res.scalar_one_or_none()
    budget_amount = float(budget.amount) if budget else 0.0

    # Calculate Reset Date (1st of next month)
    if now.month == 12:
        reset_date = datetime(now.year + 1, 1, 1)
    else:
        reset_date = datetime(now.year, now.month + 1, 1)

    # Recent Transactions (limit 10, filtered by days if provided)
    recent_stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id, *date_filter)
        .order_by(Transaction.date.desc())
        .limit(10)
    )
    recent_res = await db.execute(recent_stmt)
    recent = recent_res.scalars().all()

    return {
        "total_income": float(total_income),
        "total_expenses": float(total_expense),
        "balance": float(total_income - total_expense),
        "monthly_budget": budget_amount,
        "monthly_spent": float(monthly_spent),
        "reset_date": reset_date,
        "recent_transactions": recent,
        "days_filter": days,
    }


@router.get(
    "/income-expense-comparison", response_model=IncomeExpenseComparisonResponse
)
async def get_income_expense_comparison(
    db: DBSession,
    user_id: CurrentUserID,
    months: int = Query(
        6, ge=1, le=12, description="Number of months to retrieve (1-12)"
    ),
):
    def get_stmt(tx_type: TransactionType):
        return (
            select(
                extract("year", Transaction.date).label("year"),
                extract("month", Transaction.date).label("month"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.user_id == user_id, Transaction.type == tx_type)
            .group_by(
                extract("year", Transaction.date), extract("month", Transaction.date)
            )
            .order_by(
                extract("year", Transaction.date).desc(),
                extract("month", Transaction.date).desc(),
            )
            .limit(months)
        )

    income_res = await db.execute(get_stmt(TransactionType.INCOME))
    expense_res = await db.execute(get_stmt(TransactionType.EXPENSE))

    income_data = income_res.all()
    expense_data = expense_res.all()

    income_dict = {
        (int(row.year), int(row.month)): float(row.total) for row in income_data
    }
    expense_dict = {
        (int(row.year), int(row.month)): float(row.total) for row in expense_data
    }

    all_months = sorted(
        set(list(income_dict.keys()) + list(expense_dict.keys())), reverse=True
    )[:months]
    all_months.reverse()

    result = []
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    for year, month in all_months:
        month_label = f"{month_names[month - 1]} {year}"
        result.append(
            IncomeExpenseDataPoint(
                month=month_label,
                income=income_dict.get((year, month), 0.0),
                expense=expense_dict.get((year, month), 0.0),
            )
        )

    return IncomeExpenseComparisonResponse(data=result)


@router.get("/dashboard-summary")
async def get_dashboard_summary(
    db: DBSession,
    user_id: CurrentUserID,
    months: int = Query(
        6, ge=1, le=12, description="Number of months to retrieve (1-12)"
    ),
):
    stmt = (
        select(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            Transaction.category,
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .where(Transaction.user_id == user_id)
        .group_by(
            extract("year", Transaction.date),
            extract("month", Transaction.date),
            Transaction.category,
            Transaction.type,
        )
        .order_by(
            desc(extract("year", Transaction.date)),
            desc(extract("month", Transaction.date)),
        )
    )

    result_proxy = await db.execute(stmt)
    raw_data = result_proxy.all()

    result = process_dashboard_summary(raw_data, months)

    return {"data": result}


@router.get("/category-proportions")
async def get_category_proportions(
    db: DBSession,
    user_id: CurrentUserID,
    type: TransactionType = Query(..., description="Transaction type"),
):

    stmt = (
        select(Transaction.category, func.sum(Transaction.amount).label("total"))
        .where(Transaction.user_id == user_id, Transaction.type == type)
        .group_by(Transaction.category)
        .order_by(desc("total"))
    )

    result_proxy = await db.execute(stmt)
    raw_data = result_proxy.all()

    data = []
    for row in raw_data:
        data.append({"category": str(row.category), "total": float(row.total)})

    return {"data": data}


@router.post("/scan")
async def scan_receipt(
    file: UploadFile,
    db: DBSession,
    user_id: CurrentUserID,
):
    if (
        not file.filename
        or not file.content_type
        or not file.content_type.startswith("image/")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image with a valid filename",
        )

    # 1. Save File
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)

    file_ext = Path(cast(str, file.filename)).suffix
    file_name = f"{uuid.uuid4()}{file_ext}"
    full_path = upload_path / file_name

    image_data = await file.read()
    with full_path.open("wb") as buffer:
        buffer.write(image_data)

    file_url = f"/uploads/receipts/{file_name}"

    # 2. Get User Categories for context
    stmt = select(Category.name).where(
        Category.user_id == user_id, Category.type == TransactionType.EXPENSE
    )
    result = await db.execute(stmt)
    cat_names = list(result.scalars().all())

    if DEFAULT_CATEGORY not in cat_names:
        cat_names.append(DEFAULT_CATEGORY)

    # 3. AI Analysis
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt = f"""
    Analyze this receipt image and break it down into logical expense items based on their categories.
    
    Rules:
    1. Identify items on the receipt and group them by these categories: {cat_names}.
    2. If multiple items belong to the same category (e.g., Maggi and Milk both in 'Groceries'), you can group them into one line item.
    3. For each item/group, extract the specific amount.
    4. The sum of all items must equal the grand total on the receipt.
    5. Use '{DEFAULT_CATEGORY}' if an item doesn't fit anywhere else.
    6. Extract the transaction date.

    Return the data structured as a list of items, each with item_name, amount, category, and note.
    """

    try:
        image_part = types.Part.from_bytes(data=image_data, mime_type=file.content_type)

        def _generate_receipt_analysis():
            return client.models.generate_content(
                model=settings.GEMINI_MODEL_ID,
                contents=[image_part, prompt],
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": MultiReceiptAnalysis.model_json_schema(),
                },
            )

        response = await run_sync(_generate_receipt_analysis)

        if not response.text:
            raise ValueError("Empty response from AI")

        analysis = MultiReceiptAnalysis.model_validate_json(response.text)
        return {
            "receipt_url": file_url,
            "date": analysis.date,
            "total_on_receipt": analysis.total_amount_on_receipt,
            "suggested_transactions": analysis.items,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan receipt: {str(e)}",
        )
