from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/news_db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create base class for models
Base = declarative_base()

def get_utc_now():
    """Get current UTC time as timezone-naive datetime"""
    return datetime.utcnow()

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content = Column(Text)
    summary = Column(Text)
    author = Column(String(200))
    image_url = Column(String(500))
    language = Column(String(10), default="en")
    published_at = Column(DateTime)
    source = Column(String(100))
    source_api = Column(String(50))
    categories = Column(JSON, default=list)
    extraction_error = Column(Text)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Create tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Drop tables (for testing)
async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) 