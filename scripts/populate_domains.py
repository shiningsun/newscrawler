#!/usr/bin/env python3
"""
Script to populate domain column for existing articles.
"""

import sys
import os

# Add the project root to the path (parent directory of scripts)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import AsyncSessionLocal, Article

import asyncio
import asyncpg
from urllib.parse import urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def populate_existing_domains():
    """
    Connects to the database, fetches articles with a null domain,
    parses the domain from the URL, and updates the record.
    """
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/news_db")
    logger.info(f"Connecting to database at {database_url.split('@')[-1]}...")

    conn = None
    try:
        conn = await asyncpg.connect(database_url)
        logger.info("Database connection successful.")

        # Fetch articles where the domain is not yet set
        articles_to_update = await conn.fetch("SELECT id, url FROM articles WHERE domain IS NULL")

        if not articles_to_update:
            logger.info("No articles found with a missing domain. Database is already up-to-date.")
            return

        logger.info(f"Found {len(articles_to_update)} articles with a missing domain. Starting update process...")
        updated_count = 0

        for article in articles_to_update:
            article_id = article['id']
            url = article['url']

            if not url:
                logger.warning(f"Skipping article ID {article_id} due to missing URL.")
                continue

            try:
                # Extract the domain from the URL
                domain = urlparse(url).netloc
                if domain:
                    # Update the article record with the new domain
                    await conn.execute(
                        "UPDATE articles SET domain = $1 WHERE id = $2",
                        domain,
                        article_id
                    )
                    logger.info(f"Updated domain for article ID {article_id} to '{domain}'")
                    updated_count += 1
                else:
                    logger.warning(f"Could not extract domain from URL for article ID {article_id}: {url}")
            except Exception as e:
                logger.error(f"Failed to process article ID {article_id}: {e}")

        logger.info(f"Successfully updated {updated_count} out of {len(articles_to_update)} articles.")

    except Exception as e:
        logger.error(f"An error occurred during the database operation: {e}")
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    asyncio.run(populate_existing_domains()) 