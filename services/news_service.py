from typing import Optional, Dict, List
from datetime import datetime, timedelta
from services.apis.news_sources import fetch_thenewsapi_articles, fetch_gnews_articles, fetch_nytimes_articles
from utils.article_extractor import extract_multiple_articles
import requests

class NewsService:
    def __init__(self):
        # Map source names to fetch functions
        self.source_strategies = {
            "thenewsapi": fetch_thenewsapi_articles,
            "gnews": fetch_gnews_articles,
            "nytimes": fetch_nytimes_articles,
        }

    def get_news(
        self,
        categories: Optional[str] = None,
        language: str = "en",
        search: Optional[str] = None,
        domains: Optional[str] = None,
        published_after: Optional[str] = None,
        extract: bool = True,
        sources: Optional[str] = None
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
                    articles, meta_info = fetch_func(categories, language, search, domains, published_after)
                else:
                    articles, meta_info = fetch_func(language, search, published_after)
                news_articles.extend(articles)
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
            raise Exception(f"Error fetching news: {str(e)}") 