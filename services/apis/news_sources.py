import requests
from datetime import datetime
from config import THENEWSAPI_TOKEN, GNEWS_API_KEY, NYTIMES_API_KEY

def fetch_thenewsapi_articles(categories=None, language="en", search=None, domains=None, published_after=None):
    url = "https://api.thenewsapi.com/v1/news/top"
    params = {
        "api_token": THENEWSAPI_TOKEN,
        "language": language,
        "published_after": published_after
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
    articles = data.get("data", [])
    for article in articles:
        article['source_api'] = 'thenewsapi'
    return articles, data.get("meta", {})

def fetch_gnews_articles(language="en", search=None, published_after=None):
    url = "https://gnews.io/api/v4/search"
    params = {
        "apikey": GNEWS_API_KEY,
        "lang": language,
        "country": "us",
        "max": 10
    }
    if search:
        params["q"] = "newsweek AND " + search
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
    articles = data.get("articles", [])
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

def fetch_nytimes_articles(language="en", search=None, published_after=None):
    url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    params = {
        "api-key": NYTIMES_API_KEY,
        "sort": "newest"
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
    articles = data.get("response", {}).get("docs", [])
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