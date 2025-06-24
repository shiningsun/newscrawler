import asyncio
import asyncpg
import os
import logging

try:
    from config import EXCLUDED_DOMAINS
except ImportError:
    # Default list if not defined in config
    EXCLUDED_DOMAINS = [
        "youtube.com",
        "twitter.com",
        "facebook.com",
        "instagram.com",
        "reddit.com",
    ]

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def remove_excluded_articles():
    """
    Connects to the database and removes articles from domains
    on the exclusion list.
    """
    if not EXCLUDED_DOMAINS:
        logger.info("Exclusion list is empty. No domains to remove.")
        return

    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/news_db")
    logger.info(f"Connecting to database at {database_url.split('@')[-1]}...")

    conn = None
    try:
        conn = await asyncpg.connect(database_url)
        logger.info("Database connection successful.")

        # Build the WHERE clause dynamically to match domains and subdomains
        conditions = []
        params = []
        for i, domain in enumerate(EXCLUDED_DOMAINS, 1):
            conditions.append(f"(domain = ${i*2-1} OR domain LIKE ${i*2})")
            params.extend([domain, f"%.{domain}"])
        
        where_clause = " OR ".join(conditions)
        
        # First, count the articles that will be deleted
        count_query = f"SELECT COUNT(*) FROM articles WHERE {where_clause}"
        articles_to_delete = await conn.fetchval(count_query, *params)

        if articles_to_delete == 0:
            logger.info("No articles found from excluded domains. Database is clean.")
            return

        logger.info(f"Found {articles_to_delete} articles from excluded domains. Proceeding with deletion...")

        # Execute the DELETE statement
        delete_query = f"DELETE FROM articles WHERE {where_clause}"
        status = await conn.execute(delete_query, *params)
        
        deleted_count = int(status.split(' ')[-1])
        logger.info(f"Successfully deleted {deleted_count} articles from the database.")

    except Exception as e:
        logger.error(f"An error occurred during the database operation: {e}")
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    asyncio.run(remove_excluded_articles()) 