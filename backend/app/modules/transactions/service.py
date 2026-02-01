import uuid
import shutil
from pathlib import Path
from typing import Optional, List
from sqlalchemy.orm import Session
from google.genai import types
from .repository import TransactionRepository
from .models import Transaction
from .schemas import (
    TransactionCreate,
    TransactionResponse,
    IncomeExpenseDataPoint,
    ReceiptAnalysis,
)
from app.core.config import settings
from app.modules.chatbot.service import ChatbotService
from app.modules.categories.repository import CategoryRepository


class TransactionService:
    def __init__(self, repo: TransactionRepository, db: Session):
        self.repo = repo
        self.db = db
        self.chatbot_service = ChatbotService()
        self.cat_repo = CategoryRepository(db)

    def create_user_transaction(
        self, user_id: str, data: TransactionCreate
    ) -> Transaction:
        """Create a new transaction for a user"""
        return self.repo.create(user_id, data)

    def get_user_transactions(
        self, user_id: str, type: Optional[str] = None
    ) -> List[Transaction]:
        """Get all transactions for a user, optionally filtered by type"""
        return self.repo.get_by_user(user_id, type)

    def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get a transaction by its ID"""
        return self.repo.get_by_id(transaction_id)

    def delete_transaction(self, transaction_id: str) -> bool:
        """Delete a transaction by ID"""
        return self.repo.delete_by_id(transaction_id)

    def get_transaction_response(self, transaction: Transaction) -> TransactionResponse:
        """Convert Transaction model to TransactionResponse"""
        return TransactionResponse(
            id=transaction.id,
            amount=transaction.amount,
            type=transaction.type,
            category=transaction.category,
            note=transaction.note,
            date=transaction.date,
            receipt_url=transaction.receipt_url,
            created_at=transaction.created_at,
        )

    def get_user_stats(self, user_id: str) -> dict:
        """Get dashboard statistics for a user"""
        stats = self.repo.get_user_stats(user_id)
        stats["recent_transactions"] = [
            self.get_transaction_response(t) for t in stats["recent_transactions"]
        ]
        return stats

    def get_income_expense_comparison(
        self, user_id: str, months: int = 6
    ) -> list[IncomeExpenseDataPoint]:
        """Get monthly income vs expense comparison data"""
        return self.repo.get_income_expense_comparison(user_id, months)

    def get_dashboard_summary(self, user_id: str, months: int = 6) -> list[dict]:
        """Get detailed summary for dashboard chart: stacked expenses by category + income line"""
        raw_data = self.repo.get_detailed_summary(user_id, months)

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

        summary = {}
        for row in raw_data:
            year = int(row.year)
            month = int(row.month)
            month_key = f"{year}-{month:02d}"
            month_label = f"{month_names[month - 1]} {year}"

            if month_key not in summary:
                summary[month_key] = {"month": month_label, "Income": 0.0}

            if row.type == "income":
                current_income = summary[month_key].get("Income", 0.0)
                if isinstance(current_income, (int, float)):
                    summary[month_key]["Income"] = current_income + float(row.total)
                else:
                    summary[month_key]["Income"] = float(row.total)
            else:
                category_name = row.category
                summary[month_key][category_name] = float(row.total)

        result = []
        for month_key in sorted(summary.keys()):
            month_data = summary[month_key]
            if month_data["Income"] == 0:
                month_data["Income"] = 0.0
            result.append(month_data)

        return result

    def get_category_proportions(self, user_id: str, tx_type: str) -> list[dict]:
        """Get category proportions for income or expense"""
        raw_data = self.repo.get_category_proportions(user_id, tx_type)

        result = []
        for row in raw_data:
            try:
                category = row.category
                total = row.total
            except AttributeError:
                category = row[0]
                total = row[1]

            result.append({"category": str(category), "total": float(total)})

        return result

    def scan_receipt(
        self, user_id: str, file_bytes: bytes, content_type: str
    ) -> ReceiptAnalysis:
        """Scan receipt image using Gemini Vision API with structured output"""
        user_categories = self.cat_repo.get_by_user(user_id, type="expense")
        cat_names = [c.name for c in user_categories]

        if "Others" not in cat_names:
            cat_names.append("Others")

        prompt = f"""
        Analyze this receipt image and extract the following information:
        
        1. Amount: The total grand amount shown on the receipt (as a number)
        2. Date: The date of the transaction in YYYY-MM-DD format
        3. Category: Choose exactly one from this list: {cat_names}. If the receipt does not fit any, choose 'Others'.
        4. Note: Any additional relevant details from the receipt (optional, can be null if nothing notable)
        
        Return only these fields: amount, date, category, and note.
        """

        try:
            image_part = types.Part.from_bytes(data=file_bytes, mime_type=content_type)

            response = self.chatbot_service.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image_part, prompt],
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": ReceiptAnalysis.model_json_schema(),
                },
            )

            return ReceiptAnalysis.model_validate_json(response.text)
        except Exception as e:
            raise Exception(f"Failed to scan receipt: {str(e)}")

    def save_receipt_file(self, file) -> str:
        """Save uploaded receipt file and return the URL path"""
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

        file_extension = Path(file.filename).suffix
        filename = f"{uuid.uuid4()}{file_extension}"
        file_path = Path(settings.UPLOAD_DIR) / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"/uploads/receipts/{filename}"
