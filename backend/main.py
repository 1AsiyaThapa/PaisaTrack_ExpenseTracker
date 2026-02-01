import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine

import app.modules.auth.models
import app.modules.categories.models
import app.modules.transactions.models
import app.modules.users.models

from app.modules.auth.routes import router as auth_router
from app.modules.categories.routes import router as cat_router
from app.modules.chatbot.routes import router as chat_router
from app.modules.transactions.routes import router as tx_router
from app.modules.users.routes import router as users_router

Base.metadata.create_all(bind=engine)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(tx_router, prefix="/transactions", tags=["Transactions"])
app.include_router(cat_router, prefix="/categories", tags=["Categories"])
app.include_router(chat_router, prefix="/chatbot", tags=["Chatbot"])


@app.get("/")
def root():
    return {"message": "PaisaTrack API is running"}
