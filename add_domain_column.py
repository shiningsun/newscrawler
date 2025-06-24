import asyncio
import asyncpg
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def add_domain_column():
    """
    Connects to the database and adds the 'domain' column to the 'articles' table
    if it does not already exist.
    """
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/news_db")
    logger.info(f"Connecting to database at {database_url.split('@')[-1]}...")

    conn = None
    try:
        conn = await asyncpg.connect(database_url)
        logger.info("Database connection successful.")

        # Use ALTER TABLE ... ADD COLUMN IF NOT EXISTS for PostgreSQL 9.6+
        # For broader compatibility, we'll check first.
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
               SELECT 1
               FROM information_schema.columns
               WHERE table_name = 'articles' AND column_name = 'domain'
            );
        """)

        if column_exists:
            logger.info("The 'domain' column already exists in the 'articles' table.")
        else:
            logger.info("The 'domain' column does not exist. Adding it now...")
            # Add the 'domain' column to the 'articles' table
            await conn.execute("ALTER TABLE articles ADD COLUMN domain VARCHAR(255)")
            logger.info("Successfully added the 'domain' column to the 'articles' table.")

    except Exception as e:
        logger.error(f"An error occurred during the database operation: {e}")
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    asyncio.run(add_domain_column()) 