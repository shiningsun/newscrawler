from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import logging
import random
import time
from utils.article_extractor import extract_article_content
from googlenewsdecoder import gnewsdecoder

logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
]

def _get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.google.com/',
        'Cookie': 'CONSENT=YES+1'
    }

# In-memory cache for category links, to avoid scraping them on every call
_google_category_links_cache = {}

def _get_google_news_category_links(language: str) -> Dict[str, str]:
    """
    Scrapes the Google News homepage to dynamically find category URLs.
    Results are cached in memory to avoid repeated requests.
    """
    if language in _google_category_links_cache:
        return _google_category_links_cache[language]

    home_url = f"https://news.google.com/home?hl={language}&gl=US&ceid=US:{language}"
    headers = _get_random_headers()
    
    category_links = {'home': home_url}
    
    try:
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(home_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
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

def _resolve_publisher_url(google_news_url: str) -> Optional[str]:
    try:
        decoded = gnewsdecoder(google_news_url)
        if decoded.get("status"):
            return decoded["decoded_url"]
        else:
            logger.warning(f"Decoder error: {decoded.get('message')}")
            return None
    except Exception as e:
        logger.warning(f"Failed to decode Google News URL {google_news_url}: {e}")
        return None

def _scrape_google_news_page(url: str, language: str, limit: int) -> List[Dict[str, any]]:
    headers = _get_random_headers()
    
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
                try:
                    time.sleep(random.uniform(0.5, 1.5)) # Add delay before each extraction
                    logger.info(f"Resolving publisher URL from: {article_url}")
                    publisher_url = _resolve_publisher_url(article_url)
                    if not publisher_url:
                        logger.warning(f"Could not resolve publisher URL for {article_url}, skipping.")
                        continue
                    logger.info(f"Extracting content from publisher URL: {publisher_url}")
                    extracted_data = extract_article_content(publisher_url)
                    
                    if extracted_data.get('error'):
                        logger.warning(f"Skipping article from {publisher_url} due to extraction error: {extracted_data.get('error')}")
                        continue

                    final_url = extracted_data.get('url')

                    article_data = {
                        'uuid': final_url, # Use final publisher URL
                        'title': extracted_data.get('title') or title,
                        'description': extracted_data.get('summary', ''),
                        'content': extracted_data.get('content', ''),
                        'author': extracted_data.get('author', ''),
                        'url': final_url, # Use final publisher URL
                        'image_url': '', 
                        'language': language,
                        'published_at': published_at,
                        'source': source,
                        'categories': ['general'],
                        'source_api': 'googlenews',
                        'extraction_error': extracted_data.get('error')
                    }
                    articles.append(article_data)
                except Exception as e:
                    logger.warning(f"Failed to process or extract content from {article_url}: {e}")

        return articles

    try:
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = parse_articles(soup)
        seen_urls = set(a['url'] for a in articles)

        for item in soup.find_all('article'):
            full_coverage_link = None
            for a in item.find_all('a'):
                if a.text.strip().lower() == 'full coverage':
                    full_coverage_link = a.get('href')
                    break
            if full_coverage_link and full_coverage_link.startswith('./articles/'):
                fc_url = 'https://news.google.com' + full_coverage_link[1:]
                try:
                    time.sleep(random.uniform(0.5, 1.5))
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

def fetch_googlenews_articles(
    categories: Optional[str] = None,
    language: str = "en",
    limit: int = 10
) -> Tuple[List[Dict[str, any]], Dict[str, any]]:
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