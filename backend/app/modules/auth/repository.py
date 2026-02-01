import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from fastapi import HTTPException, status
from .models import EmailOTP


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def generate_otp(self) -> str:
        return str(random.randint(100000, 999999))

    def create_otp(self, email: str) -> str:
        stmt = delete(EmailOTP).where(EmailOTP.email == email)
        self.db.execute(stmt)

        otp_code = self.generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        otp_record = EmailOTP(email=email, otp_code=otp_code, expires_at=expires_at)
        self.db.add(otp_record)
        self.db.commit()

        return otp_code

    def verify_otp(self, email: str, otp_code: str) -> bool:
        stmt = select(EmailOTP).where(
            EmailOTP.email == email, EmailOTP.otp_code == otp_code
        )
        otp_record = self.db.execute(stmt).scalar_one_or_none()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code"
            )

        if datetime.now(timezone.utc) > otp_record.expires_at:
            self.db.delete(otp_record)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new one.",
            )

        self.db.delete(otp_record)
        self.db.commit()

        return True

    def cleanup_expired_otps(self):
        stmt = delete(EmailOTP).where(EmailOTP.expires_at < datetime.now(timezone.utc))
        self.db.execute(stmt)
        self.db.commit()
