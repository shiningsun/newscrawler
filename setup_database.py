#!/usr/bin/env python3
"""
Database setup script for the news crawler service
Creates the necessary tables in PostgreSQL.
"""

import asyncio
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, engine
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_database():
    """Create database tables"""
    try:
        print("Setting up database tables...")
        await create_tables()
        print("✅ Database tables created successfully!")
        
        # Test the connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version}")
            
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL environment variable")
        print("3. Ensure the database exists")
        print("4. Verify your PostgreSQL credentials")
        raise

if __name__ == "__main__":
    print("News Crawler Database Setup")
    print("=" * 40)
    
    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  DATABASE_URL not set. Using default: postgresql+asyncpg://postgres:password@localhost:5432/news_db")
        print("Set DATABASE_URL environment variable to customize the connection.")
    
    asyncio.run(setup_database()) 