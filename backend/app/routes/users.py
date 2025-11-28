from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.models import get_db, UserResponse
from app.services import user_service, auth_service

router = APIRouter()
