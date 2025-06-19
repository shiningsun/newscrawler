from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
import json
from article_extractor import extract_article_content, extract_multiple_articles
from config import THENEWSAPI_TOKEN, GNEWS_API_KEY, HOST, PORT

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
    extract: bool = Query(True, description="Extract article content (default: true)")
) -> Dict:
    try:
        # Set default published_after to yesterday if not provided
        if published_after is None:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            published_after = yesterday
        
        # First API call - TheNewsAPI
        url1 = "https://api.thenewsapi.com/v1/news/top"
        params1 = {
            "api_token": THENEWSAPI_TOKEN,
            "language": language,
            "published_after": published_after
        }
        
        # Add parameters to first API
        if categories:
            params1["categories"] = categories
        if search:
            params1["search"] = search
        if domains:
            params1["domains"] = domains
        
        # Second API call - GNews
        url2 = "https://gnews.io/api/v4/search"
        params2 = {
            "apikey": GNEWS_API_KEY,
            "lang": language,
            "country": "us",
            "max": 10
        }
        
        # Add parameters to second API
        if search:
            params2["q"] = "newsweek AND " + search
        else:
            params2["q"] = "newsweek"
        if published_after:
            # Convert YYYY-MM-DD to timestamp for GNews
            try:
                date_obj = datetime.strptime(published_after, "%Y-%m-%d")
                params2["from"] = date_obj.strftime("%Y-%m-%dT00:00:00Z")
            except:
                pass
        
        # Make both API calls
        response1 = requests.get(url1, params=params1)
        response1.raise_for_status()
        
        response2 = requests.get(url2, params=params2)
        response2.raise_for_status()
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Clear previous articles and store new ones
        news_articles.clear()
        
        # Process first API results (TheNewsAPI)
        articles1 = data1.get("data", [])
        for article in articles1:
            article['source_api'] = 'thenewsapi'
        news_articles.extend(articles1)
        
        # Process second API results (GNews)
        articles2 = data2.get("articles", [])
        for article in articles2:
            # Transform GNews format to match our structure
            transformed_article = {
                'uuid': article.get('url', ''),  # Use URL as UUID
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'image_url': article.get('image', ''),
                'language': article.get('language', language),
                'published_at': article.get('publishedAt', ''),
                'source': article.get('source', {}).get('name', ''),
                'categories': ['general'],  # GNews doesn't provide categories
                'source_api': 'gnews'
            }
            news_articles.append(transformed_article)
        
        # Print the articles in a formatted way
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
        print(f"Total articles from both APIs: {len(news_articles)}")
        
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
        print(f"TheNewsAPI - Found: {data1.get('meta', {}).get('found', 0)}, Returned: {data1.get('meta', {}).get('returned', 0)}")
        print(f"GNews - Total Results: {data2.get('totalArticles', 0)}")
        
        # Extract article content if requested and merge with articles
        if extract and news_articles:
            print(f"\n=== Extracting content from {len(news_articles)} articles ===")
            urls = [article.get('url') for article in news_articles if article.get('url')]
            if urls:
                extracted_articles = extract_multiple_articles(urls, delay=1.0)
                print(f"Successfully extracted content from {len(extracted_articles)} articles")
                
                # Merge extracted content with original articles
                for i, article in enumerate(news_articles):
                    if i < len(extracted_articles):
                        extracted_content = extracted_articles[i]
                        
                        # Add extracted content directly to article fields
                        if extracted_content.get('content'):
                            article['content'] = extracted_content.get('content')
                        
                        if extracted_content.get('summary'):
                            article['summary'] = extracted_content.get('summary')
                        
                        if extracted_content.get('author'):
                            article['author'] = extracted_content.get('author')
                        
                        # Add extraction error if any
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
            "meta": {
                "thenewsapi": data1.get("meta", {}),
                "gnews": {
                    "totalArticles": data2.get("totalArticles", 0),
                    "articles": len(articles2)
                }
            },
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