from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# 1. Create Engine
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# 2. Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 3. Base Class for Models
class Base(DeclarativeBase):
    pass


# 4. Dependency for Routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
