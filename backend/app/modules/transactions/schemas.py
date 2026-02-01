from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional
from datetime import datetime
from decimal import Decimal


class TransactionBase(BaseModel):
    amount: Decimal
    type: Literal["income", "expense"]
    category: str
    note: Optional[str] = None
    date: datetime
    receipt_url: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class ReceiptAnalysis(BaseModel):
    amount: float = Field(description="The total grand amount shown on the receipt")
    date: str = Field(description="The date of the transaction in YYYY-MM-DD format")
    category: str = Field(description="The category that best fits this receipt")
    note: Optional[str] = Field(
        default=None,
        description="Any additional notes or details from the receipt (optional)",
    )


class IncomeExpenseDataPoint(BaseModel):
    month: str
    income: float
    expense: float


class IncomeExpenseComparisonResponse(BaseModel):
    data: list[IncomeExpenseDataPoint]
