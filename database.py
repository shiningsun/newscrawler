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
    url = Column(String(5000), unique=True, index=True, nullable=False)
    domain = Column(String(255), index=True, nullable=True)
    title = Column(String(5000), nullable=False)
    description = Column(Text)
    content = Column(Text)
    summary = Column(Text)
    author = Column(String(2000))
    image_url = Column(String(5000))
    language = Column(String(10), default="en")
    published_at = Column(DateTime)
    source = Column(String(1000))
    source_api = Column(String(500))
    categories = Column(JSON, default=list)
    extraction_error = Column(Text)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class Transcript(Base):
    __tablename__ = "transcript"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(5000), nullable=True)
    url = Column(String(5000), unique=True, index=True, nullable=False)
    published_date = Column(DateTime)
    content = Column(Text, nullable=False)
    author = Column(String(2000))
    domain = Column(String(255), index=True, nullable=True)
    category = Column(String(255), index=True, nullable=True)
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