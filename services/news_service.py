from typing import Optional, Dict, List
from datetime import datetime, timedelta
from services.apis.news_sources import fetch_thenewsapi_articles, fetch_gnews_articles, fetch_nytimes_articles, fetch_guardian_articles
from utils.article_extractor import get_or_extract_article_content
import requests
from motor.motor_asyncio import AsyncIOMotorCollection

class NewsService:
    def __init__(self, news_collection: AsyncIOMotorCollection):
        self.news_collection = news_collection
        # Map source names to fetch functions
        self.source_strategies = {
            "thenewsapi": fetch_thenewsapi_articles,
            "gnews": fetch_gnews_articles,
            "nytimes": fetch_nytimes_articles,
            "guardian": fetch_guardian_articles,
        }

    async def get_news(
        self,
        categories: Optional[str] = None,
        language: str = "en",
        search: Optional[str] = None,
        domains: Optional[str] = None,
        published_after: Optional[str] = None,
        extract: bool = True,
        sources: Optional[str] = None,
        limit: int = 10
    ) -> Dict:
        try:
            if published_after is None:
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                published_after = yesterday

            all_sources = set(self.source_strategies.keys())
            if sources:
                selected_sources = set(s.strip().lower() for s in sources.split(",") if s.strip()) & all_sources
                if not selected_sources:
                    selected_sources = all_sources
            else:
                selected_sources = all_sources

            news_articles = []
            meta = {}

            for source in selected_sources:
                fetch_func = self.source_strategies[source]
                if source == "thenewsapi":
                    articles, meta_info = fetch_func(categories, language, search, domains, published_after, limit)
                else:
                    articles, meta_info = fetch_func(language=language, search=search, published_after=published_after, limit=limit)
                news_articles.extend(articles)
                meta[source] = meta_info

            # Save articles to MongoDB
            if news_articles:
                for article in news_articles:
                    # Use URL as the unique identifier
                    await self.news_collection.update_one(
                        {'_id': article['url']},
                        {'$set': article},
                        upsert=True
                    )

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
                print(f"\n=== Extracting content for {len(news_articles)} articles (using cache if available) ===")
                for article in news_articles:
                    url = article.get('url')
                    if not url:
                        continue
                    
                    try:
                        extracted_content, source = await get_or_extract_article_content(url, self.news_collection)
                        print(f"Content for '{article.get('title')}' from {source}")
                        
                        if extracted_content:
                            article.update({
                                'content': extracted_content.get('content'),
                                'summary': extracted_content.get('summary'),
                                'author': extracted_content.get('author'),
                                'extraction_error': extracted_content.get('error')
                            })
                    except Exception as e:
                        print(f"Error extracting content for {url}: {e}")
                        article['extraction_error'] = str(e)

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
            raise Exception(f"Error fetching news: {str(e)}") 