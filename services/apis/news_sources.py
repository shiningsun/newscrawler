import requests
from datetime import datetime
from config import THENEWSAPI_TOKEN, GNEWS_API_KEY, NYTIMES_API_KEY, GUARDIAN_API_KEY
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)

# In-memory cache for category links, to avoid scraping them on every call
_google_category_links_cache = {}

def fetch_thenewsapi_articles(categories=None, language="en", search=None, domains=None, published_after=None, limit=10):
    url = "https://api.thenewsapi.com/v1/news/top"
    params = {
        "api_token": THENEWSAPI_TOKEN,
        "language": language,
        "published_after": published_after,
        "limit": limit
    }
    if categories:
        params["categories"] = categories
    if search:
        params["search"] = search
    if domains:
        params["domains"] = domains
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    articles = data.get("data", [])[:limit]  # Ensure we don't exceed limit
    for article in articles:
        article['source_api'] = 'thenewsapi'
    return articles, data.get("meta", {})

def fetch_gnews_articles(language="en", search=None, published_after=None, limit=10):
    url = "https://gnews.io/api/v4/search"
    params = {
        "apikey": GNEWS_API_KEY,
        "lang": language,
        "country": "us",
        "max": limit
    }
    
    query = ""
    if search:
        # If search is a comma-separated list or multiple words, join with ' AND '
        if ',' in search:
            search_terms = [s.strip() for s in search.split(',') if s.strip()]
            query = ' AND '.join(search_terms)
        elif ' ' in search.strip():
            search_terms = [s.strip() for s in search.strip().split() if s.strip()]
            query = ' AND '.join(search_terms)
        else:
            query = search
        
        if "newsweek" not in query.lower():
            params["q"] = query + " AND newsweek"
        else:
            params["q"] = query
    else:
        params["q"] = "newsweek"
        
    if published_after:
        try:
            date_obj = datetime.strptime(published_after, "%Y-%m-%d")
            params["from"] = date_obj.strftime("%Y-%m-%dT00:00:00Z")
        except:
            pass
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    articles = data.get("articles", [])[:limit]  # Ensure we don't exceed limit
    transformed = []
    for article in articles:
        transformed_article = {
            'uuid': article.get('url', ''),
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'url': article.get('url', ''),
            'image_url': article.get('image', ''),
            'language': article.get('language', language),
            'published_at': article.get('publishedAt', ''),
            'source': article.get('source', {}).get('name', ''),
            'categories': ['general'],
            'source_api': 'gnews'
        }
        transformed.append(transformed_article)
    return transformed, {"totalArticles": data.get("totalArticles", 0), "articles": len(articles)}

def fetch_nytimes_articles(language="en", search=None, published_after=None, limit=10):
    url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    params = {
        "api-key": NYTIMES_API_KEY,
        "sort": "newest",
        "page-size": limit
    }
    if search:
        params["q"] = search
    if published_after:
        try:
            date_obj = datetime.strptime(published_after, "%Y-%m-%d")
            params["begin_date"] = date_obj.strftime("%Y%m%d")
        except:
            pass
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    articles = data.get("response", {}).get("docs", [])[:limit]  # Ensure we don't exceed limit
    transformed = []
    for article in articles:
        multimedia = article.get('multimedia', [])
        if multimedia and isinstance(multimedia, list):
            img_url = multimedia[0].get('url', '')
            if img_url and not img_url.startswith('http'):
                img_url = 'https://www.nytimes.com/' + img_url
        else:
            img_url = ''
        transformed_article = {
            'uuid': article.get('_id', ''),
            'title': article.get('headline', {}).get('main', ''),
            'description': article.get('abstract', ''),
            'url': article.get('web_url', ''),
            'image_url': img_url,
            'language': language,
            'published_at': article.get('pub_date', ''),
            'source': 'nytimes.com',
            'categories': [kw.get('value', '') for kw in article.get('keywords', [])] if article.get('keywords') else ['general'],
            'source_api': 'nytimes'
        }
        transformed.append(transformed_article)
    return transformed, {"totalArticles": len(articles)}

def fetch_guardian_articles(language="en", search=None, published_after=None, limit=10):
    url = "https://content.guardianapis.com/search"
    params = {
        "api-key": GUARDIAN_API_KEY,
        "order-by": "newest",
        "page-size": limit,
        "show-fields": "trailText,headline,byline,thumbnail,bodyText,publication"
    }
    if search:
        params["q"] = search
    if published_after:
        try:
            # Guardian expects YYYY-MM-DD or ISO8601
            date_obj = datetime.strptime(published_after, "%Y-%m-%d")
            params["from-date"] = date_obj.strftime("%Y-%m-%d")
        except:
            pass
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    results = data.get("response", {}).get("results", [])[:limit]  # Ensure we don't exceed limit
    articles = []
    for article in results:
        fields = article.get("fields", {})
        transformed_article = {
            'uuid': article.get('id', ''),
            'title': fields.get('headline', article.get('webTitle', '')),
            'description': fields.get('trailText', ''),
            'url': article.get('webUrl', ''),
            'image_url': fields.get('thumbnail', ''),
            'language': language,  # Guardian API does not provide language
            'published_at': article.get('webPublicationDate', ''),
            'source': 'theguardian.com',
            'categories': [article.get('sectionName', 'general')],
            'source_api': 'guardian'
        }
        articles.append(transformed_article)
    meta = {
        "total": data.get("response", {}).get("total", 0),
        "pageSize": data.get("response", {}).get("pageSize", 0),
        "currentPage": data.get("response", {}).get("currentPage", 0)
    }
    return articles, meta

def _get_google_news_category_links(language: str) -> Dict[str, str]:
    """
    Scrapes the Google News homepage to dynamically find category URLs.
    Results are cached in memory to avoid repeated requests.
    """
    if language in _google_category_links_cache:
        return _google_category_links_cache[language]

    home_url = f"https://news.google.com/home?hl={language}&gl=US&ceid=US:{language}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': f'{language}-US,{language};q=0.9'
    }
    
    category_links = {'home': home_url}
    
    try:
        response = requests.get(home_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # This selector targets the main navigation bar for categories.
        # It's based on current structure and might need updates if Google changes its frontend.
        nav_container = soup.find('div', jsname='r2235c')
        if nav_container:
            links = nav_container.find_all('a', class_='SFllF')
            for link in links:
                name = link.text.strip().lower().replace('u.s.', 'us')
                href = link.get('href')
                if name and href and href.startswith('./topics/'):
                    full_url = 'https://news.google.com' + href[1:]
                    category_links[name] = full_url
        
        _google_category_links_cache[language] = category_links
        logger.info(f"Dynamically scraped Google News categories for '{language}': {list(category_links.keys())}")
        return category_links

    except Exception as e:
        logger.error(f"Could not dynamically scrape Google News categories: {e}. Falling back to 'home' only.")
        category_links['home'] = home_url # Fallback
        return category_links

def _scrape_google_news_page(url: str, language: str, limit: int) -> List[Dict[str, any]]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': f'{language}-US,{language};q=0.9'
    }
    
    def parse_articles(soup):
        articles = []
        for item in soup.find_all('article'):
            title_elem = item.find('a', class_='gPFEn') or item.find('h3')
            if not title_elem:
                continue
            title = title_elem.get_text()
            relative_url = title_elem.get('href')
            article_url = 'https://news.google.com' + relative_url[1:] if relative_url and relative_url.startswith('./') else relative_url
            source_elem = item.find('div', class_='bInWSc')
            source = source_elem.get_text() if source_elem else 'Unknown Source'
            time_elem = item.find('time', class_='hvbAAd')
            published_at = time_elem['datetime'] if time_elem and 'datetime' in time_elem.attrs else datetime.utcnow().isoformat()
            if article_url:
                articles.append({
                    'uuid': article_url, 'title': title, 'description': '', 'url': article_url,
                    'image_url': '', 'language': language, 'published_at': published_at,
                    'source': source, 'categories': ['general'], 'source_api': 'googlenews'
                })
        return articles

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = parse_articles(soup)
        seen_urls = set(a['url'] for a in articles)

        # Find and follow 'Full Coverage' links for each article
        for item in soup.find_all('article'):
            full_coverage_link = None
            # Look for anchor tags with 'Full Coverage' text
            for a in item.find_all('a'):
                if a.text.strip().lower() == 'full coverage':
                    full_coverage_link = a.get('href')
                    break
            if full_coverage_link and full_coverage_link.startswith('./articles/'):
                fc_url = 'https://news.google.com' + full_coverage_link[1:]
                try:
                    fc_resp = requests.get(fc_url, headers=headers, timeout=15)
                    fc_resp.raise_for_status()
                    fc_soup = BeautifulSoup(fc_resp.content, 'html.parser')
                    fc_articles = parse_articles(fc_soup)
                    for fc_article in fc_articles:
                        if fc_article['url'] not in seen_urls:
                            articles.append(fc_article)
                            seen_urls.add(fc_article['url'])
                except Exception as e:
                    logger.warning(f"Failed to scrape Full Coverage page {fc_url}: {e}")

        return articles[:limit]
    except Exception as e:
        logger.error(f"Error scraping Google News page {url}: {e}")
        return []

def fetch_googlenews_articles(categories: Optional[str] = None, language: str = "en", limit: int = 10) -> (List[Dict[str, any]], Dict[str, any]):
    """
    Scrapes Google News for top stories from specified categories or the homepage.
    Category links are fetched dynamically.
    """
    google_news_categories = _get_google_news_category_links(language)
    
    if categories:
        selected_cats = [c.strip().lower() for c in categories.split(',') if c.strip().lower() in google_news_categories]
        if not selected_cats:
            selected_cats = ['home']
    else:
        selected_cats = ['home']

    all_articles = []
    for category in selected_cats:
        url = google_news_categories[category]
        logger.info(f"Scraping Google News category '{category}' from URL: {url}")
        articles_from_cat = _scrape_google_news_page(url, language, limit)
        all_articles.extend(articles_from_cat)

    all_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
    final_articles = all_articles[:limit]
    
    meta = {"totalArticles": len(final_articles), "note": "Scraped from Google News. May be unstable."}
    return final_articles, meta

engine = create_async_engine(
    "postgresql+asyncpg://user:password@host/dbname",
    pool_size=20,           # default is usually 5 or 10
    max_overflow=10,        # allows extra connections above pool_size
) 