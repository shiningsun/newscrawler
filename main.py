from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
import json
from utils.article_extractor import extract_article_content, extract_multiple_articles, get_or_extract_article_content
from config import THENEWSAPI_TOKEN, GNEWS_API_KEY, NYTIMES_API_KEY, HOST, PORT
from services.news_service import NewsService
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Python Service",
    description="A basic Python service using FastAPI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "news_db")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

def get_news_collection():
    return db.news_articles

news_service = NewsService(get_news_collection())

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to the Python Service!"}

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}

@app.get("/news")
async def get_news(
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    language: str = Query("en", description="Language code (default: en)"),
    search: Optional[str] = Query(None, description="Search term to filter articles"),
    domains: Optional[str] = Query(None, description="Comma-separated list of domains to filter by"),
    published_after: str = Query(default=None, description="Filter articles published after this date (YYYY-MM-DD format, default: yesterday)"),
    extract: bool = Query(True, description="Extract article content (default: true)"),
    sources: Optional[str] = Query(None, description="Comma-separated list of sources to use: thenewsapi,gnews,nytimes,guardian (default: all)"),
    limit: int = Query(10, description="Maximum number of articles to fetch from each source (default: 10)")
) -> Dict:
    """
    Fetch news articles from selected sources (TheNewsAPI, GNews, NYTimes, Guardian).
    """
    try:
        return await news_service.get_news(
            categories=categories,
            language=language,
            search=search,
            domains=domains,
            published_after=published_after,
            extract=extract,
            sources=sources,
            limit=limit
        )
    except Exception as e:
        logger.error(f"An error occurred in /news endpoint: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/extract-article")
async def extract_single_article(
    url: str = Query(..., description="URL of the article to extract content from"),
    force_extract: bool = Query(False, description="Force extraction from the web and update the cache.")
) -> Dict:
    """
    Extract content from a single article URL, using MongoDB for caching.
    """
    try:
        news_collection = get_news_collection()
        
        content, source = await get_or_extract_article_content(url, news_collection, force_extract)
        
        return {
            "status": "success",
            "source": source,
            "article": content
        }
    except Exception as e:
        logger.error(f"Error extracting article content: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error extracting article content: {str(e)}")

@app.get("/extract-articles")
async def extract_articles_from_news(
    limit: Optional[int] = Query(5, description="Number of articles to extract (default: 5)"),
    delay: float = Query(1.0, description="Delay between requests in seconds (default: 1.0)"),
    force_extract: bool = Query(False, description="Force extraction from the web and update the cache.")
) -> Dict:
    """
    Extract content from the most recent news articles, using MongoDB for caching.
    """
    try:
        news_collection = get_news_collection()
        # Get URLs from the stored news articles
        cursor = news_collection.find({}, {"url": 1, "_id": 0}).limit(limit)
        urls = [article.get('url') for article in await cursor.to_list(length=limit) if article.get('url')]

        if not urls:
            raise HTTPException(status_code=400, detail="No valid URLs found in news articles.")

        logger.info(f"Extracting content from {len(urls)} articles...")

        extracted_articles = []
        for url in urls:
            content, _ = await get_or_extract_article_content(url, news_collection, force_extract)
            extracted_articles.append(content)

        return {
            "status": "success",
            "articles_extracted": len(extracted_articles),
            "articles": extracted_articles
        }
    except Exception as e:
        logger.error(f"Error extracting articles: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error extracting articles: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True) 