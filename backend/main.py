from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import Base, engine
from app.routes import auth, users, transactions, categories, chatbot

# Create tables
Base.metadata.create_all(bind=engine)

# App
app = FastAPI(title="PaisaTrack API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/users")
app.include_router(transactions.router, prefix="/transactions")
app.include_router(categories.router, prefix="/categories")
app.include_router(chatbot.router, prefix="/chatbot")


@app.get("/")
def root():
    return {"message": "PaisaTrack API is running"}
