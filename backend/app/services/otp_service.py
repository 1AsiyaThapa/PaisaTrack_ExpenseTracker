import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import EmailOTP


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def create_otp(db: Session, email: str) -> str:
    db.query(EmailOTP).filter(EmailOTP.email == email).delete()
    
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    otp_record = EmailOTP(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()
    
    return otp_code


def verify_otp(db: Session, email: str, otp_code: str) -> bool:
    otp_record = db.query(EmailOTP).filter(
        EmailOTP.email == email,
        EmailOTP.otp_code == otp_code
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    if datetime.utcnow() > otp_record.expires_at:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one."
        )
    
    db.delete(otp_record)
    db.commit()
    
    return True


def cleanup_expired_otps(db: Session):
    db.query(EmailOTP).filter(EmailOTP.expires_at < datetime.utcnow()).delete()
    db.commit()
