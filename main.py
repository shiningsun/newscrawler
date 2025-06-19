from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
import json
from article_extractor import extract_article_content, extract_multiple_articles
from config import THENEWSAPI_TOKEN, GNEWS_API_KEY, NYTIMES_API_KEY, HOST, PORT
from news_api import fetch_thenewsapi_articles, fetch_gnews_articles, fetch_nytimes_articles

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

# Store news articles
news_articles: List[Dict] = []

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
    sources: Optional[str] = Query(None, description="Comma-separated list of sources to use: thenewsapi,gnews,nytimes (default: all)")
) -> Dict:
    try:
        if published_after is None:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            published_after = yesterday

        # Determine which sources to use
        all_sources = {"thenewsapi", "gnews", "nytimes"}
        if sources:
            selected_sources = set(s.strip().lower() for s in sources.split(",") if s.strip()) & all_sources
            if not selected_sources:
                selected_sources = all_sources
        else:
            selected_sources = all_sources

        news_articles = []
        meta = {}

        # Fetch from TheNewsAPI
        if "thenewsapi" in selected_sources:
            articles1, meta1 = fetch_thenewsapi_articles(categories, language, search, domains, published_after)
            news_articles.extend(articles1)
            meta["thenewsapi"] = meta1
        # Fetch from GNews
        if "gnews" in selected_sources:
            articles2, meta2 = fetch_gnews_articles(language, search, published_after)
            news_articles.extend(articles2)
            meta["gnews"] = meta2
        # Fetch from NYTimes
        if "nytimes" in selected_sources:
            articles3, meta3 = fetch_nytimes_articles(language, search, published_after)
            news_articles.extend(articles3)
            meta["nytimes"] = meta3

        # Print the articles in a formatted way (optional, for debug)
        print("\n=== Latest News Articles ===")
        print(f"Language: {language}")
        if categories:
            print(f"Filtered by categories: {categories}")
        if search:
            print(f"Search term: {search}")
        if domains:
            print(f"Filtered by domains: {domains}")
        print(f"Published after: {published_after}")
        print(f"Extract content: {extract}")
        print(f"Sources: {', '.join(selected_sources)}")
        print(f"Total articles from selected APIs: {len(news_articles)}")
        for idx, article in enumerate(news_articles, 1):
            print(f"\nArticle {idx} (from {article.get('source_api', 'unknown')}):")
            print(f"Title: {article.get('title', 'N/A')}")
            print(f"Source: {article.get('source', 'N/A')}")
            print(f"Description: {article.get('description', 'N/A')}")
            print(f"URL: {article.get('url', 'N/A')}")
            print(f"Published: {article.get('published_at', 'N/A')}")
            print(f"Categories: {', '.join(article.get('categories', []))}")
            print(f"Language: {article.get('language', 'N/A')}")
            print("-" * 80)
        print(f"\nTotal articles fetched: {len(news_articles)}")
        for k, v in meta.items():
            print(f"{k} meta: {v}")

        # Extract article content if requested and merge with articles
        if extract and news_articles:
            print(f"\n=== Extracting content from {len(news_articles)} articles ===")
            urls = [article.get('url') for article in news_articles if article.get('url')]
            if urls:
                extracted_articles = extract_multiple_articles(urls, delay=1.0)
                print(f"Successfully extracted content from {len(extracted_articles)} articles")
                for i, article in enumerate(news_articles):
                    if i < len(extracted_articles):
                        extracted_content = extracted_articles[i]
                        if extracted_content.get('content'):
                            article['content'] = extracted_content.get('content')
                        if extracted_content.get('summary'):
                            article['summary'] = extracted_content.get('summary')
                        if extracted_content.get('author'):
                            article['author'] = extracted_content.get('author')
                        if extracted_content.get('error'):
                            article['extraction_error'] = extracted_content.get('error')
                    else:
                        article['extraction_error'] = "Failed to extract content"

        return {
            "status": "success",
            "language": language,
            "categories_filter": categories,
            "search_term": search,
            "domains_filter": domains,
            "published_after": published_after,
            "extract_content": extract,
            "sources": list(selected_sources),
            "meta": meta,
            "articles": news_articles
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

@app.get("/extract-article")
async def extract_single_article(url: str = Query(..., description="URL of the article to extract content from")) -> Dict:
    """
    Extract content from a single article URL.
    """
    try:
        content = extract_article_content(url)
        return {
            "status": "success",
            "article": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting article content: {str(e)}")

@app.get("/extract-articles")
async def extract_articles_from_news(
    limit: Optional[int] = Query(5, description="Number of articles to extract (default: 5)"),
    delay: float = Query(1.0, description="Delay between requests in seconds (default: 1.0)")
) -> Dict:
    """
    Extract content from the most recent news articles.
    """
    try:
        if not news_articles:
            raise HTTPException(status_code=400, detail="No news articles available. Please fetch news first using /news endpoint.")
        
        # Get URLs from the stored news articles
        urls = [article.get('url') for article in news_articles[:limit] if article.get('url')]
        
        if not urls:
            raise HTTPException(status_code=400, detail="No valid URLs found in news articles.")
        
        print(f"\n=== Extracting content from {len(urls)} articles ===")
        
        # Extract content from multiple articles
        extracted_articles = extract_multiple_articles(urls, delay)
        
        return {
            "status": "success",
            "articles_extracted": len(extracted_articles),
            "articles": extracted_articles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting articles: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True) 