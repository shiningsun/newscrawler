#!/usr/bin/env python3
"""
Script to set up the transcript table in the database
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from the main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import create_tables, engine
from logging_config import setup_logging, get_logger

async def setup_transcript_table():
    """Create the transcript table in the database"""
    
    # Setup logging
    setup_logging(log_level="INFO", app_name="setup_transcript_table")
    logger = get_logger(__name__)
    
    try:
        logger.info("Creating database tables...")
        await create_tables()
        logger.info("Database tables created successfully!")
        
        # Test the connection
        async with engine.begin() as conn:
            # Check if the transcript table exists
            result = await conn.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'transcript')")
            table_exists = result.scalar()
            
            if table_exists:
                logger.info("✓ Transcript table exists in the database")
                
                # Get table info
                result = await conn.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'transcript' ORDER BY ordinal_position")
                columns = result.fetchall()
                
                logger.info("Transcript table columns:")
                for column_name, data_type in columns:
                    logger.info(f"  - {column_name}: {data_type}")
            else:
                logger.error("✗ Transcript table was not created")
                
    except Exception as e:
        logger.error(f"Error setting up transcript table: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_transcript_table()) 