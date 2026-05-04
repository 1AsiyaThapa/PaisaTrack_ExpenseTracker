import asyncio
import random
from datetime import datetime
from decimal import Decimal

import numpy as np
from dateutil.relativedelta import relativedelta
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal, Base, engine
from app.modules.categories.models import Category  # noqa: F401
from app.modules.transactions.models import Transaction, TransactionType
from app.modules.users.models import User

np.random.seed(42)

MONTHS_TO_GENERATE = 24
BASE_INCOME = 65000
BASE_EXPENSE_RATIO = 0.45
FESTIVAL_MONTHS = {10, 11}

EXPENSE_CATEGORIES = [
    "Groceries",
    "Transport",
    "Entertainment",
    "Shopping",
    "Utilities",
]
INCOME_CATEGORIES = ["Salary", "Freelance"]


async def seed_yearly_data(email: str):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        user = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if not user:
            print(f"User {email} not found! Please create an account first.")
            return

        await session.execute(
            delete(Transaction).where(
                Transaction.user_id == user.id,
                Transaction.note.like("Auto-generated%"),
            )
        )
        await session.flush()
        print("Cleared old auto-generated transactions.")

        now = datetime.now()
        prev_expense = BASE_INCOME * BASE_EXPENSE_RATIO

        print(
            f"Generating {MONTHS_TO_GENERATE} months of synthetic data for {email}..."
        )

        for i in range(MONTHS_TO_GENERATE, 0, -1):
            target_date = now - relativedelta(months=i)
            month = target_date.month

            # --- INCOME ---
            salary = BASE_INCOME + np.random.normal(0, 2000)
            freelance = float(
                np.random.choice(
                    [0, 0, 8000, 12000, 5000], p=[0.3, 0.2, 0.2, 0.15, 0.15]
                )
            )
            total_income = salary + freelance

            session.add(
                Transaction(
                    user_id=user.id,
                    amount=Decimal(str(round(salary, 2))),
                    type=TransactionType.INCOME,
                    category="Salary",
                    date=target_date.replace(day=1),
                    note=f"Auto-generated for {target_date.strftime('%b %Y')}",
                )
            )

            if freelance > 0:
                session.add(
                    Transaction(
                        user_id=user.id,
                        amount=Decimal(str(round(freelance, 2))),
                        type=TransactionType.INCOME,
                        category="Freelance",
                        date=target_date.replace(day=random.randint(10, 25)),
                        note=f"Auto-generated for {target_date.strftime('%b %Y')}",
                    )
                )

            # --- EXPENSES ---
            base_expense = total_income * BASE_EXPENSE_RATIO

            festival_bump = (
                base_expense * np.random.uniform(0.25, 0.40)
                if month in FESTIVAL_MONTHS
                else 0
            )

            autocorr_pull = prev_expense * 0.3
            inflation = (MONTHS_TO_GENERATE - i) * 150
            noise = np.random.normal(0, 1800)

            total_expense = (
                base_expense + festival_bump + autocorr_pull + inflation + noise
            )
            total_expense = max(8000, total_expense)
            prev_expense = total_expense

            num_tx = random.randint(8, 18)
            for j in range(num_tx):
                amount = total_expense / num_tx + random.randint(-300, 300)
                amount = max(50, amount)
                session.add(
                    Transaction(
                        user_id=user.id,
                        amount=Decimal(str(round(amount, 2))),
                        type=TransactionType.EXPENSE,
                        category=random.choice(EXPENSE_CATEGORIES),
                        date=target_date.replace(day=random.randint(1, 28)),
                        note=f"Auto-generated for {target_date.strftime('%b %Y')}",
                    )
                )

        await session.commit()
        print("ML Demo data generated successfully!")


if __name__ == "__main__":
    asyncio.run(seed_yearly_data("np03cs4a230383@heraldcollege.edu.np"))
