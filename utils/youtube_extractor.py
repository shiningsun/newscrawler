import requests
from bs4 import BeautifulSoup
import time
import random
import re
import logging
from typing import Dict, Optional
from urllib.parse import urlparse
from datetime import datetime
import dateutil.parser

logger = logging.getLogger(__name__)

# Configuration for YouTube scraping
YOUTUBE_CONFIG = {
    'min_delay': 2.0,
    'max_delay': 5.0,
    'timeout': 15,
    'max_retries': 3,
}

# Realistic user agents for YouTube
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

def _get_random_headers():
    """Generate realistic headers for YouTube scraping"""
    user_agent = random.choice(USER_AGENTS)
    
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    return headers

def _add_random_delay():
    """Add a random delay to simulate human behavior"""
    delay = random.uniform(YOUTUBE_CONFIG['min_delay'], YOUTUBE_CONFIG['max_delay'])
    time.sleep(delay)

def _clean_text(text: str) -> str:
    """Clean and sanitize text content"""
    if not text:
        return ""
    
    try:
        # Convert to string if it's not already
        text = str(text)
        
        # Remove null bytes and other invalid UTF-8 characters
        text = text.replace('\x00', '')
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
        try:
            # Remove all non-printable characters
            text = ''.join(char for char in text if char.isprintable() or char.isspace())
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
            return text.strip()
        except Exception:
            return ""

def extract_youtube_metadata(url: str) -> Dict:
    """
    Extract metadata from a YouTube video URL.
    Returns a dictionary with title, author, published_date, and other metadata.
    """
    try:
        # Validate YouTube URL
        if not _is_valid_youtube_url(url):
            return {
                'title': '',
                'author': '',
                'published_date': None,
                'description': '',
                'view_count': '',
                'like_count': '',
                'url': url,
                'error': 'Invalid YouTube URL'
            }
        
        # Add random delay
        _add_random_delay()
        
        # Create session with retry logic
        session = requests.Session()
        session.headers.update(_get_random_headers())
        
        # Make the request with better encoding handling
        response = session.get(
            url, 
            timeout=YOUTUBE_CONFIG['timeout'],
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Try to detect encoding properly
        if response.encoding == 'ISO-8859-1':
            response.encoding = 'utf-8'
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title with multiple approaches
        title = _extract_title(soup, response.text)
        
        # Extract author/channel name
        author = _extract_author(soup, response.text)
        
        # Extract published date
        published_date = _extract_published_date(soup, response.text)
        
        # Extract description
        description = _extract_description(soup, response.text)
        
        # Extract view count
        view_count = _extract_view_count(response.text)
        
        # Extract like count
        like_count = _extract_like_count(response.text)
        
        return {
            'title': title,
            'author': author,
            'published_date': published_date,
            'description': description,
            'view_count': view_count,
            'like_count': like_count,
            'url': response.url,
            'error': None
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
        return {
            'title': '',
            'author': '',
            'published_date': None,
            'description': '',
            'view_count': '',
            'like_count': '',
            'url': url,
            'error': f'HTTP error {e.response.status_code}: {str(e)}'
        }
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error for {url}: {e}")
        return {
            'title': '',
            'author': '',
            'published_date': None,
            'description': '',
            'view_count': '',
            'like_count': '',
            'url': url,
            'error': f'Connection error: {str(e)}'
        }
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error for {url}")
        return {
            'title': '',
            'author': '',
            'published_date': None,
            'description': '',
            'view_count': '',
            'like_count': '',
            'url': url,
            'error': 'Request timeout'
        }
    except Exception as e:
        logger.error(f"Error extracting YouTube metadata from {url}: {e}")
        return {
            'title': '',
            'author': '',
            'published_date': None,
            'description': '',
            'view_count': '',
            'like_count': '',
            'url': url,
            'error': str(e)
        }

def _is_valid_youtube_url(url: str) -> bool:
    """Check if the URL is a valid YouTube video URL"""
    try:
        parsed = urlparse(url)
        return (
            parsed.netloc in ['www.youtube.com', 'youtube.com', 'm.youtube.com'] and
            '/watch' in parsed.path
        )
    except Exception:
        return False

def _extract_title(soup: BeautifulSoup, html_text: str) -> str:
    """Extract video title from YouTube page"""
    title = ""
    
    # Try the new YouTube structure first
    title_selectors = [
        'ytd-watch-metadata yt-formatted-string',
        'ytd-watch-metadata h1 yt-formatted-string',
        'ytd-watch-metadata #title h1 yt-formatted-string',
        'ytd-watch-metadata #title',
        'ytd-watch-metadata h1',
        'yt-formatted-string[class*="title"]',
        'h1 yt-formatted-string',
        'h1.ytd-video-primary-info-renderer',
        'h1.ytd-watch-metadata',
    ]
    
    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem:
            title = title_elem.get_text().strip()
            if title:
                break
    
    # Try meta tags as fallback
    if not title:
        meta_selectors = [
            'meta[property="og:title"]',
            'meta[name="title"]',
            'meta[property="twitter:title"]',
        ]
        
        for selector in meta_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get('content', '').strip()
                if title:
                    break
    
    # Try title tag as last resort
    if not title:
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            # Remove " - YouTube" suffix
            title = title.replace(' - YouTube', '')
    
    # Try regex patterns from page source
    if not title:
        try:
            # Look for title in various JSON patterns
            patterns = [
                r'"title":"([^"]+)"',
                r'"videoTitle":"([^"]+)"',
                r'"name":"([^"]+)"',
                r'"text":"([^"]+)"',
            ]
            for pattern in patterns:
                title_match = re.search(pattern, html_text)
                if title_match:
                    title = title_match.group(1)
                    # Clean up any HTML entities
                    title = title.replace('\\u0026', '&').replace('\\/', '/')
                    break
        except Exception:
            pass
    
    return _clean_text(title)

def _extract_author(soup: BeautifulSoup, html_text: str) -> str:
    """Extract channel name/author from YouTube page"""
    author = ""
    
    # Try the new YouTube structure first
    author_selectors = [
        'ytd-watch-metadata ytd-channel-name a',
        'ytd-watch-metadata ytd-channel-name yt-formatted-string',
        'ytd-watch-metadata #channel-name a',
        'ytd-watch-metadata #owner-name a',
        'ytd-channel-name a',
        'ytd-channel-name yt-formatted-string',
        'a.ytd-channel-name',
        'yt-formatted-string[class*="channel"]',
        'yt-formatted-string[class*="owner"]',
    ]
    
    for selector in author_selectors:
        author_elem = soup.select_one(selector)
        if author_elem:
            author = author_elem.get_text().strip()
            if author:
                break
    
    # Try meta tags as fallback
    if not author:
        meta_selectors = [
            'meta[name="author"]',
            'meta[property="og:site_name"]',
            'link[rel="author"]',
        ]
        
        for selector in meta_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get('content', author_elem.get('href', '')).strip()
                if author:
                    break
    
    # Try regex patterns from page source
    if not author:
        try:
            # Look for channel name in various patterns
            patterns = [
                r'"author":"([^"]+)"',
                r'"channelName":"([^"]+)"',
                r'"ownerChannelName":"([^"]+)"',
                r'"ownerName":"([^"]+)"',
                r'"channel":"([^"]+)"',
            ]
            for pattern in patterns:
                author_match = re.search(pattern, html_text)
                if author_match:
                    author = author_match.group(1)
                    # Clean up any HTML entities
                    author = author.replace('\\u0026', '&').replace('\\/', '/')
                    break
        except Exception:
            pass
    
    return _clean_text(author)

def _extract_published_date(soup: BeautifulSoup, html_text: str) -> Optional[datetime]:
    """Extract published date from YouTube page"""
    published_date = None
    
    # Try meta tags
    date_selectors = [
        'meta[property="article:published_time"]',
        'meta[name="date"]',
        'meta[itemprop="datePublished"]',
        'time[datetime]',
    ]
    
    for selector in date_selectors:
        date_elem = soup.select_one(selector)
        if date_elem:
            date_str = date_elem.get('content') or date_elem.get('datetime')
            if date_str:
                try:
                    published_date = dateutil.parser.parse(date_str)
                    break
                except Exception:
                    continue
    
    # Try regex patterns from page source
    if not published_date:
        try:
            # Look for date patterns in the page source
            patterns = [
                r'"uploadDate":"([^"]+)"',
                r'"publishedTimeText":"([^"]+)"',
                r'([A-Za-z]{3}\s+\d{1,2},\s+\d{4})',  # "Jan 15, 2024"
                r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})',  # "15 Jan 2024"
            ]
            for pattern in patterns:
                date_match = re.search(pattern, html_text)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        published_date = dateutil.parser.parse(date_str)
                        break
                    except Exception:
                        continue
        except Exception:
            pass
    
    return published_date

def _extract_description(soup: BeautifulSoup, html_text: str) -> str:
    """Extract video description from YouTube page"""
    description = ""
    
    # Try meta tags
    desc_selectors = [
        'meta[property="og:description"]',
        'meta[name="description"]',
        'meta[property="twitter:description"]',
    ]
    
    for selector in desc_selectors:
        desc_elem = soup.select_one(selector)
        if desc_elem:
            description = desc_elem.get('content', '').strip()
            if description:
                break
    
    # Try regex pattern from page source
    if not description:
        try:
            desc_match = re.search(r'"description":"([^"]+)"', html_text)
            if desc_match:
                description = desc_match.group(1)
        except Exception:
            pass
    
    return _clean_text(description)

def _extract_view_count(html_text: str) -> str:
    """Extract view count from YouTube page"""
    view_count = ""
    
    try:
        # Look for view count patterns in the page source
        patterns = [
            r'"viewCount":"(\d+)"',
            r'"view_count":"(\d+)"',
            r'"views":"(\d+)"',
            r'"viewCountText":"([^"]+)"',
            r'(\d+(?:,\d+)*)\s+views',
            r'(\d+(?:,\d+)*)\s+view',
        ]
        for pattern in patterns:
            view_match = re.search(pattern, html_text)
            if view_match:
                view_count = view_match.group(1)
                # Clean up any formatting
                view_count = view_count.replace(',', '')
                break
    except Exception:
        pass
    
    return view_count

def _extract_like_count(html_text: str) -> str:
    """Extract like count from YouTube page"""
    like_count = ""
    
    try:
        # Look for like count patterns in the page source
        patterns = [
            r'"likeCount":"(\d+)"',
            r'"like_count":"(\d+)"',
            r'"likes":"(\d+)"',
            r'"likeCountText":"([^"]+)"',
            r'(\d+(?:,\d+)*)\s+likes',
            r'(\d+(?:,\d+)*)\s+like',
        ]
        for pattern in patterns:
            like_match = re.search(pattern, html_text)
            if like_match:
                like_count = like_match.group(1)
                # Clean up any formatting
                like_count = like_count.replace(',', '')
                break
    except Exception:
        pass
    
    return like_count 