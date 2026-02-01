from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, extract, delete, desc
from decimal import Decimal
from .models import Transaction
from .schemas import TransactionCreate, IncomeExpenseDataPoint


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(
        self, user_id: str, type: Optional[str] = None
    ) -> List[Transaction]:
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        if type:
            stmt = stmt.where(Transaction.type == type)
        return list(
            self.db.execute(stmt.order_by(Transaction.date.desc())).scalars().all()
        )

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        return self.db.get(Transaction, transaction_id)

    def create(self, user_id: str, data: TransactionCreate) -> Transaction:
        transaction = Transaction(user_id=user_id, **data.model_dump())
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def delete_by_id(self, transaction_id: str) -> bool:
        stmt = delete(Transaction).where(Transaction.id == transaction_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def get_user_stats(self, user_id: str) -> dict:
        income_stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id, Transaction.type == "income"
        )
        expense_stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id, Transaction.type == "expense"
        )

        total_income = self.db.execute(income_stmt).scalar() or Decimal("0")
        total_expense = self.db.execute(expense_stmt).scalar() or Decimal("0")

        recent_stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.date.desc())
            .limit(5)
        )
        recent = self.db.execute(recent_stmt).scalars().all()

        return {
            "total_income": float(total_income),
            "total_expenses": float(total_expense),
            "balance": float(total_income - total_expense),
            "recent_transactions": list(recent),
        }

    def get_income_expense_comparison(
        self, user_id: str, months: int = 6
    ) -> list[IncomeExpenseDataPoint]:
        income_stmt = (
            select(
                extract("year", Transaction.date).label("year"),
                extract("month", Transaction.date).label("month"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.user_id == user_id, Transaction.type == "income")
            .group_by(
                extract("year", Transaction.date), extract("month", Transaction.date)
            )
            .order_by(
                extract("year", Transaction.date).desc(),
                extract("month", Transaction.date).desc(),
            )
            .limit(months)
        )

        expense_stmt = (
            select(
                extract("year", Transaction.date).label("year"),
                extract("month", Transaction.date).label("month"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.user_id == user_id, Transaction.type == "expense")
            .group_by(
                extract("year", Transaction.date), extract("month", Transaction.date)
            )
            .order_by(
                extract("year", Transaction.date).desc(),
                extract("month", Transaction.date).desc(),
            )
            .limit(months)
        )

        income_data = self.db.execute(income_stmt).all()
        expense_data = self.db.execute(expense_stmt).all()

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

        return result

    def get_detailed_summary(self, user_id: str, months: int = 6):
        """Get expenses and income grouped by month and category"""
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

        results = self.db.execute(stmt).all()

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

        unique_months = sorted(
            set((int(row.year), int(row.month)) for row in results), reverse=True
        )[:months]
        unique_months.reverse()

        filtered_results = [
            row for row in results if (int(row.year), int(row.month)) in unique_months
        ]

        return filtered_results

    def get_category_proportions(self, user_id: str, tx_type: str):
        """Get the total amount for each category for a specific transaction type"""
        stmt = (
            select(Transaction.category, func.sum(Transaction.amount).label("total"))
            .where(Transaction.user_id == user_id, Transaction.type == tx_type)
            .group_by(Transaction.category)
            .order_by(desc("total"))
        )

        return self.db.execute(stmt).all()
