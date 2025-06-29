from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
import json
from utils.article_extractor import extract_article_content, extract_multiple_articles, get_or_extract_article_content
from config import THENEWSAPI_TOKEN, GNEWS_API_KEY, NYTIMES_API_KEY, HOST, PORT
from services.news_service import NewsService
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, create_tables, Article, Transcript, AsyncSessionLocal
from sqlalchemy import select, or_, func, and_
import os
import logging
import logging.handlers
import traceback
from services.apis.google_news_crawler import fetch_googlenews_articles, getTopHeadlines
from utils.url_utils import is_domain_excluded
from urllib.parse import urlparse
import re
import asyncio
import sys
from utils.network_utils import setup_asyncio_exception_handling
from logging_config import setup_logging, get_logger
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional as OptionalType
from bs4 import BeautifulSoup
import dateutil.parser
from utils.youtube_extractor import extract_youtube_metadata

# Initialize logging
setup_logging(log_level="INFO", app_name="news_crawler")
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    # Setup asyncio exception handling to suppress network warnings
    setup_asyncio_exception_handling()
    
    # Create database tables
    await create_tables()
    logger.info("Database tables created successfully")
    logger.info("Server startup complete. Watching for file changes...")
    yield
    # Shutdown logic goes here
    logger.info("Server shutting down.")


app = FastAPI(
    title="Python Service",
    description="A basic Python service using FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    limit: int = Query(10, description="Maximum number of articles to fetch from each source (default: 10)"),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Fetch news articles from selected sources (TheNewsAPI, GNews, NYTimes, Guardian).
    """
    try:
        news_service = NewsService(db)
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
    force_extract: bool = Query(False, description="Force extraction from the web and update the cache."),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Extract content from a single article URL, using SQL database for caching.
    """
    try:
        content, source = await get_or_extract_article_content(url, db, force_extract)
        
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
    force_extract: bool = Query(False, description="Force extraction from the web and update the cache."),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Extract content from the most recent news articles, using SQL database for caching.
    """
    try:
        # Get URLs from the stored news articles
        stmt = select(Article.url).limit(limit)
        result = await db.execute(stmt)
        urls = [row[0] for row in result.fetchall() if row[0]]

        if not urls:
            raise HTTPException(status_code=400, detail="No valid URLs found in news articles.")

        logger.info(f"Extracting content from {len(urls)} articles...")

        extracted_articles = []
        for url in urls:
            content, _ = await get_or_extract_article_content(url, db, force_extract)
            extracted_articles.append(content)

        return {
            "status": "success",
            "articles_extracted": len(extracted_articles),
            "articles": extracted_articles
        }
    except Exception as e:
        logger.error(f"Error extracting articles: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error extracting articles: {str(e)}")

@app.get("/crawlnews")
async def crawl_google_news(
    categories: Optional[str] = Query(None, description="Comma-separated list of Google News categories to crawl (e.g. 'us,world,technology'). If not provided, all available categories will be crawled."),
    language: str = Query("en", description="Language code (default: en)"),
    limit: int = Query(300, description="Maximum number of articles to fetch from each category (default: 300)"),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Crawl Google News categories and load articles into SQL database.
    Only articles with content of at least 1000 characters are considered.
    If no categories are specified, all available categories will be crawled.
    """
    try:
        # If no categories provided, crawl all available categories
        if not categories:
            categories = "us,world,technology,business,entertainment,health,science,sports"
        
        articles, meta = fetch_googlenews_articles(categories=categories, language=language, limit=limit)
        inserted, updated = 0, 0
        
        # Filter out articles with content < 1000 characters
        substantial_articles = [a for a in articles if a.get('content') and len(a['content']) >= 1000]
        
        # Sort by published_at (most recent first)
        substantial_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)

        # Semaphore to limit concurrency (e.g., 10 concurrent upserts)
        semaphore = asyncio.Semaphore(10)

        # Upsert logic for a single article
        async def upsert_article(article_data):
            nonlocal inserted, updated
            async with semaphore:
                try:
                    # Create a new database session for this operation
                    async with AsyncSessionLocal() as local_db:
                        # Skip if domain is excluded
                        url = article_data.get('url')
                        if is_domain_excluded(url):
                            logger.info(f"Skipping article from excluded domain: {url}")
                            return

                        # Add domain to article_data
                        if url:
                            article_data['domain'] = urlparse(url).netloc

                        # Check if article already exists
                        stmt = select(Article).where(Article.url == url)
                        result = await local_db.execute(stmt)
                        existing_article = result.scalar_one_or_none()
                        
                        if existing_article:
                            # Update existing article
                            for key, value in article_data.items():
                                if hasattr(existing_article, key):
                                    setattr(existing_article, key, value)
                            existing_article.updated_at = datetime.utcnow()
                            updated += 1
                            logger.info(f"Updated existing article: {article_data.get('title', 'Unknown')[:50]}...")
                        else:
                            # Create new article
                            new_article = Article(**article_data)
                            local_db.add(new_article)
                            inserted += 1
                            logger.info(f"Added new article: {article_data.get('title', 'Unknown')[:50]}...")
                        
                        # Commit the local session
                        await local_db.commit()
                except Exception as e:
                    logger.error(f"Error processing article {article_data.get('url', 'Unknown URL')}: {e}")
                    return

        # Run upserts concurrently
        await asyncio.gather(*(upsert_article(article) for article in substantial_articles))

        logger.info(f"Successfully processed {inserted} new articles and {updated} updated articles")
        
        return {
            "status": "success",
            "categories": categories,
            "language": language,
            "limit": limit,
            "articles_processed": len(substantial_articles),
            "inserted": inserted,
            "updated": updated,
            "meta": meta,
            "articles": substantial_articles
        }
    except Exception as e:
        logger.error(f"Error in /crawlnews endpoint: {e}")
        # Rollback session on any error
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error crawling Google News: {str(e)}")

@app.get("/search")
async def search_articles(
    q: str = Query(..., description="Comma-delimited search keywords. Articles must contain all keywords in titles, descriptions, or content."),
    limit: int = Query(20, description="Maximum number of articles to return (default: 20)"),
    offset: int = Query(0, description="Number of articles to skip for pagination (default: 0)"),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Search articles in the database for keywords in titles, descriptions, and content.
    The 'q' parameter can be a comma-delimited list of keywords.
    Returns articles that contain ALL specified keywords as whole words (case-insensitive).
    Only articles with content length of at least 800 characters are considered.
    """
    try:
        keywords = [kw.strip() for kw in q.split(',') if kw.strip()]
        if not keywords:
            raise HTTPException(status_code=400, detail="Search query 'q' parameter must contain at least one keyword.")

        # Build a list of conditions, one for each keyword.
        # An article must satisfy ALL of these conditions.
        all_keyword_conditions = []
        for keyword in keywords:
            # Create a regex pattern for whole-word, case-insensitive search
            # \y is the word boundary marker in PostgreSQL
            search_pattern = fr"\y{re.escape(keyword)}\y"
            
            # For a single keyword, it can be in any of the specified fields.
            single_keyword_condition = or_(
                Article.title.op("~*")(search_pattern),
                Article.description.op("~*")(search_pattern),
                Article.content.op("~*")(search_pattern),
                Article.author.op("~*")(search_pattern)
            )
            all_keyword_conditions.append(single_keyword_condition)

        # Combine all conditions with AND.
        # Also filter out articles with content length less than 800 characters.
        query_conditions = and_(*all_keyword_conditions, func.length(Article.content) >= 800)

        stmt = select(Article).where(query_conditions).order_by(Article.published_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        articles = result.scalars().all()
        
        # Convert SQLAlchemy objects to dictionaries
        article_list = []
        for article in articles:
            article_dict = {
                "id": article.id,
                "title": article.title,
                "description": article.description,
                "content": article.content,
                "author": article.author,
                "url": article.url,
                "image_url": article.image_url,
                "language": article.language,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "source": article.source,
                "categories": article.categories,
                "source_api": article.source_api,
                "extraction_error": article.extraction_error,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None
            }
            article_list.append(article_dict)
        
        # Get total count for pagination info using the same conditions
        count_stmt = select(func.count(Article.id)).where(query_conditions)
        
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar()
        
        return {
            "status": "success",
            "query": q,
            "total_results": total_count,
            "limit": limit,
            "offset": offset,
            "articles_found": len(article_list),
            "min_content_length": 800,
            "articles": article_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /search endpoint: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error searching articles: {str(e)}")

@app.get("/headlines")
async def get_top_headlines(
    language: str = Query("en", description="Language code (default: en)"),
    limit: int = Query(10, description="Maximum number of headline groups to return (default: 10)")
) -> Dict:
    """
    Get top headlines from Google News homepage, grouped by related stories.
    Returns a list of lists of headline titles from the 'Top stories' section.
    Each sublist contains the titles of related stories as grouped on the page.
    """
    try:
        logger.info(f"Fetching top headlines with language: {language}, limit: {limit}")
        grouped_headlines = getTopHeadlines(language=language, limit=limit)
        total_count = sum(len(group) for group in grouped_headlines)
        return {
            "status": "success",
            "language": language,
            "limit": limit,
            "headlines_group_count": len(grouped_headlines),
            "headlines_total_count": total_count,
            "headlines_grouped": grouped_headlines
        }
    except Exception as e:
        logger.error(f"Error in /headlines endpoint: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching top headlines: {str(e)}")

# Pydantic model for transcript creation
class TranscriptCreate(BaseModel):
    url: str
    content: str

@app.post("/transcript")
async def upsert_transcript(
    transcript_data: TranscriptCreate,
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Upsert a transcript into the database.
    Crawls the YouTube URL to extract title, author, and published_date. Uses provided content.
    If a transcript with the same URL already exists, it will be updated.
    Otherwise, a new transcript will be created.
    """
    try:
        # Extract domain from URL
        domain = urlparse(transcript_data.url).netloc

        # Crawl the YouTube URL for metadata
        youtube_info = extract_youtube_metadata(transcript_data.url)
        title = youtube_info.get("title") or None
        author = youtube_info.get("author") or None
        published_date = youtube_info.get("published_date")

        # Check if transcript already exists
        stmt = select(Transcript).where(Transcript.url == transcript_data.url)
        result = await db.execute(stmt)
        existing_transcript = result.scalar_one_or_none()
        
        if existing_transcript:
            # Update existing transcript
            existing_transcript.title = title
            existing_transcript.author = author
            existing_transcript.published_date = published_date
            existing_transcript.content = transcript_data.content
            existing_transcript.domain = domain
            existing_transcript.updated_at = datetime.utcnow()
            action = "updated"
            title_preview = title[:50] + "..." if title else "No title"
            logger.info(f"Updated existing transcript: {title_preview}")
        else:
            # Create new transcript
            new_transcript = Transcript(
                title=title,
                url=transcript_data.url,
                published_date=published_date,
                content=transcript_data.content,
                author=author,
                domain=domain,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_transcript)
            action = "created"
            title_preview = title[:50] + "..." if title else "No title"
            logger.info(f"Created new transcript: {title_preview}")
        
        await db.commit()
        
        return {
            "status": "success",
            "action": action,
            "title": title,
            "author": author,
            "published_date": published_date.isoformat() if published_date else None,
            "url": transcript_data.url,
            "domain": domain,
            "youtube_metadata": {
                "description": youtube_info.get("description", ""),
                "view_count": youtube_info.get("view_count", ""),
                "like_count": youtube_info.get("like_count", ""),
                "error": youtube_info.get("error")
            }
        }
        
    except Exception as e:
        logger.error(f"Error in /transcript endpoint: {traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error upserting transcript: {str(e)}")

@app.get("/transcripts")
async def get_transcripts(
    limit: int = Query(20, description="Maximum number of transcripts to return (default: 20)"),
    offset: int = Query(0, description="Number of transcripts to skip for pagination (default: 0)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    db: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Retrieve transcripts from the database with optional filtering and pagination.
    """
    try:
        # Build query with optional filters
        query = select(Transcript)
        
        if category:
            query = query.where(Transcript.category == category)
        
        if domain:
            query = query.where(Transcript.domain == domain)
        
        # Add ordering and pagination
        query = query.order_by(Transcript.published_date.desc()).offset(offset).limit(limit)
        
        result = await db.execute(query)
        transcripts = result.scalars().all()
        
        # Convert SQLAlchemy objects to dictionaries
        transcript_list = []
        for transcript in transcripts:
            transcript_dict = {
                "id": transcript.id,
                "title": transcript.title,
                "url": transcript.url,
                "published_date": transcript.published_date.isoformat() if transcript.published_date else None,
                "content": transcript.content,
                "author": transcript.author,
                "domain": transcript.domain,
                "category": transcript.category,
                "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
                "updated_at": transcript.updated_at.isoformat() if transcript.updated_at else None
            }
            transcript_list.append(transcript_dict)
        
        # Get total count for pagination info
        count_query = select(func.count(Transcript.id))
        if category:
            count_query = count_query.where(Transcript.category == category)
        if domain:
            count_query = count_query.where(Transcript.domain == domain)
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        return {
            "status": "success",
            "total_results": total_count,
            "limit": limit,
            "offset": offset,
            "transcripts_found": len(transcript_list),
            "filters": {
                "category": category,
                "domain": domain
            },
            "transcripts": transcript_list
        }
        
    except Exception as e:
        logger.error(f"Error in /transcripts endpoint: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error retrieving transcripts: {str(e)}")

if __name__ == "__main__":
    # Use an import string for app to enable reload
    # This allows Uvicorn to re-import the application when changes are detected
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True) 