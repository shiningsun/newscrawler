from typing import Optional, Dict, List
from datetime import datetime, timedelta
from services.apis.news_sources import fetch_thenewsapi_articles, fetch_gnews_articles, fetch_nytimes_articles, fetch_guardian_articles
from utils.article_extractor import get_or_extract_article_content
from utils.url_utils import is_domain_excluded
from urllib.parse import urlparse
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database import Article
import logging

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
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
                elif source == "googlenews":
                    articles, meta_info = fetch_func(categories=categories, language=language, limit=limit)
                else:
                    articles, meta_info = fetch_func(language=language, search=search, published_after=published_after, limit=limit)
                
                # Process and save each article immediately
                for article_data in articles:
                    try:
                        # Skip if domain is excluded
                        url = article_data.get('url')
                        if is_domain_excluded(url):
                            logger.info(f"Skipping article from excluded domain: {url}")
                            continue

                        # Add domain to article_data
                        if url:
                            article_data['domain'] = urlparse(url).netloc

                        # Check if article already exists
                        stmt = select(Article).where(Article.url == url)
                        result = await self.db_session.execute(stmt)
                        existing_article = result.scalar_one_or_none()
                        
                        if existing_article:
                            # Update existing article
                            for key, value in article_data.items():
                                if hasattr(existing_article, key):
                                    setattr(existing_article, key, value)
                            existing_article.updated_at = datetime.utcnow()
                        else:
                            # Create new article
                            new_article = Article(**article_data)
                            self.db_session.add(new_article)
                        
                        # Commit immediately after each article
                        await self.db_session.commit()
                        
                        # Extract content immediately if requested
                        if extract:
                            url = article_data.get('url')
                            if url:
                                try:
                                    extracted_content, source = await get_or_extract_article_content(url, self.db_session)
                                    print(f"Content for '{article_data.get('title')}' from {source}")
                                    
                                    if extracted_content:
                                        article_data.update({
                                            'content': extracted_content.get('content'),
                                            'summary': extracted_content.get('summary'),
                                            'author': extracted_content.get('author'),
                                            'extraction_error': extracted_content.get('error')
                                        })
                                        
                                except Exception as e:
                                    logger.error(f"Error extracting content for {url}: {e}")
                                    article_data['extraction_error'] = str(e)
                                    # Rollback the session to prevent transaction issues
                                    await self.db_session.rollback()
                        
                        # Add to news_articles list
                        news_articles.append(article_data)
                        
                    except Exception as e:
                        logger.error(f"Error processing article {article_data.get('url', 'unknown')}: {e}")
                        # Rollback the session to prevent transaction issues
                        await self.db_session.rollback()
                        # Continue with next article instead of failing completely
                        continue
                
                meta[source] = meta_info

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
            logger.error(f"Request error in get_news: {e}")
            # Rollback session on request errors
            await self.db_session.rollback()
            raise Exception(f"Error fetching news: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_news: {e}")
            # Rollback session on any unexpected errors
            await self.db_session.rollback()
            raise 