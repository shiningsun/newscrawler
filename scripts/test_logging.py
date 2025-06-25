#!/usr/bin/env python3
"""
Test script to demonstrate logging configuration with the Google News crawler.
"""

import sys
import os

# Add the project root to the path (parent directory of scripts)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging, get_logger
from services.apis.google_news_crawler import fetch_googlenews_articles

def main():
    """Test the logging configuration with Google News crawler"""
    
    # Setup logging with DEBUG level to see all the detailed logs
    setup_logging(log_level="DEBUG", app_name="test_crawler")
    logger = get_logger(__name__)
    
    logger.info("Starting Google News crawler test with logging")
    
    try:
        # Test the Google News crawler with business category
        logger.info("Fetching business news articles...")
        articles, meta = fetch_googlenews_articles(
            categories="business",
            language="en",
            limit=3
        )
        
        logger.info(f"Successfully fetched {len(articles)} articles")
        logger.info(f"Meta information: {meta}")
        
        # Log some details about the articles
        for i, article in enumerate(articles, 1):
            logger.info(f"Article {i}: {article.get('title', 'No title')[:50]}...")
            logger.debug(f"Article {i} URL: {article.get('url', 'No URL')}")
            logger.debug(f"Article {i} source: {article.get('source', 'No source')}")
        
        logger.info("Google News crawler test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during Google News crawler test: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 