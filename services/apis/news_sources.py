import requests
from datetime import datetime
from config import THENEWSAPI_TOKEN, GNEWS_API_KEY, NYTIMES_API_KEY

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
    if search:
        # If search is a comma-separated list or multiple words, join with ' AND '
        if ',' in search:
            search_terms = [s.strip() for s in search.split(',') if s.strip()]
            params["q"] = ' AND '.join(search_terms)
        elif ' ' in search.strip():
            search_terms = [s.strip() for s in search.strip().split() if s.strip()]
            params["q"] = ' AND '.join(search_terms)
        else:
            params["q"] = search
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
        "api-key": "aa186ad1-74c3-4a98-a447-dd90aa6afbc3",
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