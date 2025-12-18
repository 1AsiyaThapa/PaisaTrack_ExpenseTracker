"""
Database seeding script for PaisaTrack
Creates a test user and sample transactions
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Base, engine, SessionLocal, User, Transaction
from app.services.auth_service import hash_password

def seed_database():
    """Seed the database with test data"""
    db = SessionLocal()
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Check if test user already exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if test_user:
            print("Test user already exists. Deleting old data...")
            # Delete existing transactions
            db.query(Transaction).filter(Transaction.user_id == test_user.id).delete()
            db.delete(test_user)
            db.commit()
            print("Old data deleted.")
        
        # Create test user
        print("Creating test user...")
        test_user = User(
            email="test@example.com",
            name="Test User",
            password_hash=hash_password("password123")
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"Test user created: {test_user.email} (password: password123)")
        
        # Create sample transactions
        print("Creating sample transactions...")
        
        # Sample income transactions
        income_categories = ["Salary", "Freelance", "Investment", "Bonus"]
        income_amounts = [50000, 15000, 5000, 10000]
        
        for i, (category, amount) in enumerate(zip(income_categories, income_amounts)):
            transaction = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                type="income",
                category=category,
                note=f"Monthly {category.lower()}",
                date=datetime.now() - timedelta(days=30-i*7)
            )
            db.add(transaction)
        
        # Sample expense transactions
        expense_categories = ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Rent"]
        expense_amounts = [5000, 2000, 3000, 4000, 1500, 15000]
        
        for i, (category, amount) in enumerate(zip(expense_categories, expense_amounts)):
            transaction = Transaction(
                user_id=test_user.id,
                amount=Decimal(str(amount)),
                type="expense",
                category=category,
                note=f"Monthly {category.lower()} expense",
                date=datetime.now() - timedelta(days=25-i*3)
            )
            db.add(transaction)
        
        db.commit()
        print(f"Created {len(income_categories)} income and {len(expense_categories)} expense transactions")
        
        # Calculate totals
        total_income = sum(income_amounts)
        total_expenses = sum(expense_amounts)
        balance = total_income - total_expenses
        
        print("\n" + "="*50)
        print("Seeding completed successfully!")
        print("="*50)
        print(f"Test User Email: test@example.com")
        print(f"Test User Password: password123")
        print(f"\nSample Data Summary:")
        print(f"  Total Income: ₹{total_income:,}")
        print(f"  Total Expenses: ₹{total_expenses:,}")
        print(f"  Balance: ₹{balance:,}")
        print("="*50)
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting database seeding...")
    seed_database()
    print("\nDone! You can now login with test@example.com / password123")

