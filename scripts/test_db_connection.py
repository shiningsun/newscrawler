#!/usr/bin/env python3
"""
Test script for database connection.
"""

import asyncio
import os
import sys
from sqlalchemy import text

# Add the project root to the path (parent directory of scripts)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import AsyncSessionLocal, create_tables

async def test_connection():
    """Test database connection"""
    try:
        print("Testing database connection...")
        
        # Test basic connection
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            print("✓ Database connection successful!")
        
        # Test table creation
        print("Creating tables...")
        await create_tables()
        print("✓ Tables created successfully!")
        
        print("Database is ready to use!")
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection()) 