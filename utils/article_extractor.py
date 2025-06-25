import requests
from bs4 import BeautifulSoup
import time
import random
from typing import Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import Article
import logging
import re
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from collections import defaultdict
import threading

# Import configuration
try:
    from scraping_config import SCRAPING_CONFIG, USER_AGENTS, REFERERS
except ImportError:
    # Fallback configuration if config file doesn't exist
    SCRAPING_CONFIG = {
        'min_delay': 1.0,
        'max_delay': 3.0,
        'domain_rate_limit': 2.0,
        'timeout': 20,
        '403_retry_delay': (5.0, 10.0),
        '429_retry_delay': (10.0, 20.0),
        'max_retries': 3,
    }
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    ]
    REFERERS = [
        'https://www.google.com/',
        'https://www.bing.com/',
    ]

logger = logging.getLogger(__name__)

# Configuration constants
SCRAPING_CONFIG = {
    'min_delay': 1.0,           # Minimum delay between requests (seconds)
    'max_delay': 3.0,           # Maximum delay between requests (seconds)
    'domain_rate_limit': 2.0,   # Minimum interval between requests to same domain (seconds)
    'timeout': 20,              # Request timeout (seconds)
    '403_retry_delay': (5.0, 10.0),  # Delay range after 403 error (seconds)
    '429_retry_delay': (10.0, 20.0), # Delay range after 429 error (seconds)
    'max_retries': 3,           # Maximum retries for failed requests
}

# More realistic and up-to-date user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
]

# Common referrers to make requests look more natural
REFERERS = [
    'https://www.google.com/',
    'https://www.google.com/search?q=',
    'https://www.bing.com/',
    'https://duckduckgo.com/',
    'https://www.reddit.com/',
    'https://twitter.com/',
    'https://www.facebook.com/',
    'https://www.linkedin.com/',
]

# Rate limiter for domains
class DomainRateLimiter:
    def __init__(self):
        self.domain_timestamps = defaultdict(list)
        self.lock = threading.Lock()
    
    def can_request(self, domain: str, min_interval: float = None) -> bool:
        """Check if we can make a request to this domain"""
        if min_interval is None:
            min_interval = SCRAPING_CONFIG['domain_rate_limit']
            
        with self.lock:
            now = time.time()
            # Remove old timestamps (older than 60 seconds)
            self.domain_timestamps[domain] = [
                ts for ts in self.domain_timestamps[domain] 
                if now - ts < 60
            ]
            
            if not self.domain_timestamps[domain]:
                return True
            
            # Check if enough time has passed since last request
            last_request = max(self.domain_timestamps[domain])
            return (now - last_request) >= min_interval
    
    def record_request(self, domain: str):
        """Record a request to this domain"""
        with self.lock:
            self.domain_timestamps[domain].append(time.time())

# Global rate limiter instance
rate_limiter = DomainRateLimiter()

def _create_session():
    """Create a requests session with retry logic and realistic headers"""
    from utils.network_utils import create_robust_session
    return create_robust_session()

def _get_random_headers(url: str = None):
    """Generate realistic headers for web scraping"""
    user_agent = random.choice(USER_AGENTS)
    referer = random.choice(REFERERS)
    
    # Add some randomness to make requests look more human
    accept_language = random.choice([
        'en-US,en;q=0.9',
        'en-US,en;q=0.9,es;q=0.8',
        'en-US,en;q=0.9,fr;q=0.8',
        'en-GB,en;q=0.9',
        'en-CA,en;q=0.9',
    ])
    
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': accept_language,
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Charset': 'utf-8',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'Referer': referer,
    }
    
    # Add origin header if we have a referer
    if referer:
        parsed_referer = urlparse(referer)
        headers['Origin'] = f"{parsed_referer.scheme}://{parsed_referer.netloc}"
    
    return headers

def _add_random_delay():
    """Add a random delay to simulate human behavior"""
    # Random delay between configured min and max
    delay = random.uniform(SCRAPING_CONFIG['min_delay'], SCRAPING_CONFIG['max_delay'])
    time.sleep(delay)

def _wait_for_domain_rate_limit(domain: str):
    """Wait if necessary to respect rate limits for a domain"""
    while not rate_limiter.can_request(domain):
        time.sleep(0.5)  # Wait 0.5 seconds and check again
    
    rate_limiter.record_request(domain)

def _clean_text(text: str) -> str:
    """
    Clean and sanitize text content to ensure it's valid UTF-8.
    Removes invalid characters and normalizes whitespace.
    """
    if not text:
        return ""
    
    try:
        # Convert to string if it's not already
        text = str(text)
        
        # Remove null bytes and other invalid UTF-8 characters
        text = text.replace('\x00', '')
        
        # Remove other problematic characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Ensure it's valid UTF-8
        text.encode('utf-8')
        
        return text
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        logger.warning(f"Unicode error in text cleaning: {e}")
        # Try to recover by removing problematic characters
        try:
            # Remove all non-printable characters
            text = ''.join(char for char in text if char.isprintable() or char.isspace())
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
            return text.strip()
        except Exception:
            return ""

def extract_article_content(url: str) -> Dict:
    """
    Extract article content from a given URL with enhanced anti-detection measures.
    Returns a dictionary with extracted content, summary, author, and final URL.
    """
    try:
        # Parse domain for rate limiting
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Wait for domain rate limit
        _wait_for_domain_rate_limit(domain)
        
        # Add random delay before request
        _add_random_delay()
        
        # Create session with retry logic
        session = _create_session()
        
        # Get realistic headers
        headers = _get_random_headers(url)
        
        # Make the request
        response = session.get(
            url, 
            headers=headers, 
            timeout=SCRAPING_CONFIG['timeout'],  # Use configured timeout
            allow_redirects=True,
            stream=False  # Don't stream to avoid detection
        )
        response.raise_for_status()
        
        # Get the final URL after redirects
        final_url = response.url
        
        # Try to detect encoding
        if response.encoding:
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding=response.encoding)
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Extract title
        title = ""
        title_selectors = [
            'h1',
            'title',
            '[property="og:title"]',
            '[name="twitter:title"]',
            '.headline',
            '.title',
            '#title',
            '.article-title',
            '.post-title',
            '.entry-title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                if selector in ['[property="og:title"]', '[name="twitter:title"]']:
                    title = title_elem.get('content', '').strip()
                else:
                    title = title_elem.get_text().strip()
                if title:
                    break
        
        # Clean title
        title = _clean_text(title)
        
        # Extract content with improved selectors
        content = ""
        content_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '.story-body',
            '.article-body',
            '.post-body',
            'main',
            '[role="main"]',
            '.article-text',
            '.story-content',
            '.article-main',
            '.article__content',
            '.post__content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, nav, header, footer, .ad, .advertisement, .sidebar, .comments, .social-share, .related-articles, .newsletter-signup'):
                    unwanted.decompose()
                
                content = content_elem.get_text(separator=' ', strip=True)
                if len(content) > 200:  # Ensure we have substantial content
                    break
        
        # If no specific content area found, try to get main text
        if not content or len(content) < 200:
            # Remove navigation, headers, footers, etc.
            for unwanted in soup.select('nav, header, footer, .nav, .header, .footer, .menu, .sidebar, .ad, .advertisement, .comments, .social-share'):
                unwanted.decompose()
            
            # Get all paragraphs
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50])
        
        # Clean content
        content = _clean_text(content)
        
        # Extract author with improved selectors
        author = ""
        author_selectors = [
            '.author',
            '.byline',
            '[rel="author"]',
            '[class*="author"]',
            '[class*="byline"]',
            '.writer',
            '.reporter',
            '.journalist',
            '.contributor',
            '.article-author',
            '.post-author',
            '.entry-author'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text().strip()
                if author:
                    break
        
        # Clean author
        author = _clean_text(author)
        
        # Create summary (first 200 characters of content)
        summary = content[:200] + "..." if len(content) > 200 else content
        
        return {
            'title': title,
            'content': content,
            'summary': summary,
            'author': author,
            'url': final_url,
            'error': None
        }
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.warning(f"403 Forbidden for {url} - likely bot detection")
            # Add extra delay for 403 errors to avoid further blocking
            time.sleep(random.uniform(*SCRAPING_CONFIG['403_retry_delay']))
        elif e.response.status_code == 429:
            logger.warning(f"429 Too Many Requests for {url} - rate limited")
            # Add longer delay for rate limiting
            time.sleep(random.uniform(*SCRAPING_CONFIG['429_retry_delay']))
        else:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
        
        return {
            'title': '',
            'content': '',
            'summary': '',
            'author': '',
            'url': url,
            'error': str(e)
        }
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error for {url}: {e}")
        return {
            'title': '',
            'content': '',
            'summary': '',
            'author': '',
            'url': url,
            'error': f'Connection error: {str(e)}'
        }
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error for {url}")
        return {
            'title': '',
            'content': '',
            'summary': '',
            'author': '',
            'url': url,
            'error': 'Request timeout'
        }
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return {
            'title': '',
            'content': '',
            'summary': '',
            'author': '',
            'url': url,
            'error': str(e)
        }

async def get_or_extract_article_content(url: str, db_session: AsyncSession, force_extract: bool = False) -> Tuple[Dict, str]:
    """
    Get article content from cache (database) or extract it from the web.
    Returns (content_dict, source) where source is either 'cache' or 'web'.
    """
    try:
        if not force_extract:
            # Try to get from database cache
            stmt = select(Article).where(Article.url == url)
            result = await db_session.execute(stmt)
            cached_article = result.scalar_one_or_none()
            
            if cached_article and cached_article.content:
                return {
                    'title': cached_article.title,
                    'content': cached_article.content,
                    'summary': cached_article.summary,
                    'author': cached_article.author,
                    'url': cached_article.url,
                    'domain': cached_article.domain,
                    'error': cached_article.extraction_error
                }, 'cache'
        
        # Extract from web
        extracted_data = extract_article_content(url)
        final_url = extracted_data.get('url') or url
        
        # Save to database
        stmt = select(Article).where(Article.url == url)
        result = await db_session.execute(stmt)
        existing_article = result.scalar_one_or_none()
        
        if existing_article:
            # Update existing article
            existing_article.content = extracted_data.get('content')
            existing_article.summary = extracted_data.get('summary')
            existing_article.author = extracted_data.get('author')
            existing_article.extraction_error = extracted_data.get('error')
            # Update domain if not already set
            if not existing_article.domain and final_url:
                existing_article.domain = urlparse(final_url).netloc
        else:
            # Create new article entry
            new_article = Article(
                url=final_url,
                title=extracted_data.get('title', ''),
                content=extracted_data.get('content'),
                summary=extracted_data.get('summary'),
                author=extracted_data.get('author'),
                extraction_error=extracted_data.get('error'),
                domain=urlparse(final_url).netloc
            )
            db_session.add(new_article)
        
        await db_session.commit()
        
        return extracted_data, 'web'
        
    except Exception as e:
        logger.error(f"Error in get_or_extract_article_content for {url}: {e}")
        return {
            'title': '',
            'content': '',
            'summary': '',
            'author': '',
            'url': url,
            'error': str(e)
        }, 'error'

def extract_multiple_articles(urls: list, delay: float = 1.0) -> list:
    """
    Extract content from multiple URLs with a delay between requests.
    """
    results = []
    for url in urls:
        try:
            result = extract_article_content(url)
            results.append(result)
            time.sleep(delay)  # Delay between requests
        except Exception as e:
            logger.error(f"Error extracting from {url}: {e}")
            results.append({
                'title': '',
                'content': '',
                'summary': '',
                'author': '',
                'url': url,
                'error': str(e)
            })
    return results 