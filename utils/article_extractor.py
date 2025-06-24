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
    }

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
    Extract article content from a given URL.
    Returns a dictionary with extracted content, summary, author, and final URL.
    """
    try:
        headers = _get_random_headers()
        time.sleep(random.uniform(0.5, 1.5))  # Random delay to avoid being blocked
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # Get the final URL after redirects
        final_url = response.url
        
        # Try to detect encoding
        if response.encoding:
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding=response.encoding)
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
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
            '#title'
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
        
        # Extract content
        content = ""
        content_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '.story-body',
            '.article-body',
            'main',
            '[role="main"]'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, nav, header, footer, .ad, .advertisement, .sidebar'):
                    unwanted.decompose()
                
                content = content_elem.get_text(separator=' ', strip=True)
                if len(content) > 100:  # Ensure we have substantial content
                    break
        
        # If no specific content area found, try to get main text
        if not content or len(content) < 100:
            # Remove navigation, headers, footers, etc.
            for unwanted in soup.select('nav, header, footer, .nav, .header, .footer, .menu, .sidebar, .ad, .advertisement'):
                unwanted.decompose()
            
            # Get all paragraphs
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50])
        
        # Clean content
        content = _clean_text(content)
        
        # Extract author
        author = ""
        author_selectors = [
            '.author',
            '.byline',
            '[rel="author"]',
            '[class*="author"]',
            '[class*="byline"]',
            '.writer',
            '.reporter'
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