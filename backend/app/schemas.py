from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from datetime import datetime
from decimal import Decimal


class LLMRequest(BaseModel):
    prompt: str


class LLMResponse(BaseModel):
    response: str
    error: str | None = None
    debug_info: str | None = None


class ChatRouting(BaseModel):
    intent: Literal["chat", "query"] = Field(
        description="Use 'chat' for greetings or general talk. Use 'query' if the user asks for financial data/stats."
    )
    sql: str | None = Field(
        None, description="The SQL SELECT query. Required if intent is 'query'."
    )
    chat_response: str | None = Field(
        None,
        description="A friendly conversational response. Required if intent is 'chat'.",
    )


class ResponseBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: str
    name: str
    picture: str | None = None


class SignupRequest(UserBase):
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class UserResponse(UserBase, ResponseBase):
    id: str
    google_id: str | None = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TransactionCreate(BaseModel):
    amount: Decimal
    type: Literal["income", "expense"]
    category: str
    note: str | None = None
    date: datetime


class TransactionResponse(ResponseBase):
    id: str
    amount: Decimal
    type: str
    category: str
    note: str | None = None
    date: datetime
    created_at: datetime


class IncomeExpenseDataPoint(BaseModel):
    month: str
    income: float
    expense: float


class IncomeExpenseComparisonResponse(BaseModel):
    data: list[IncomeExpenseDataPoint]


class CategoryCreate(BaseModel):
    name: str
    type: Literal["income", "expense"]
    icon: str
    color: str | None = None


class CategoryResponse(ResponseBase):
    id: str
    name: str
    type: str
    icon: str
    color: str | None = None
    created_at: datetime


class OTPRequest(BaseModel):
    email: str
    name: str


class OTPVerifyRequest(BaseModel):
    email: str
    name: str
    password: str
    otp_code: str


class UserUpdate(BaseModel):
    name: str | None = None
    password: str | None = None
    new_password: str | None = None
