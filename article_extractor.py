import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional, List
import time
from urllib.parse import urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArticleExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_article_content(self, url: str) -> Dict[str, str]:
        """
        Extract article content from a given URL.
        
        Args:
            url (str): The URL of the article to extract content from
            
        Returns:
            Dict[str, str]: Dictionary containing extracted content with keys:
                - title: Article title
                - content: Main article content
                - summary: Article summary/description
                - author: Article author (if found)
                - published_date: Publication date (if found)
                - error: Error message if extraction failed
        """
        try:
            logger.info(f"Extracting content from: {url}")
            
            # Make request to the URL
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract summary/description
            summary = self._extract_summary(soup)
            
            # Extract author
            author = self._extract_author(soup)
            
            # Extract published date
            published_date = self._extract_published_date(soup)
            
            return {
                'title': title,
                'content': content,
                'summary': summary,
                'author': author,
                'published_date': published_date,
                'url': url,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return {
                'title': None,
                'content': None,
                'summary': None,
                'author': None,
                'published_date': None,
                'url': url,
                'error': str(e)
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title from the page."""
        # Try different selectors for title
        title_selectors = [
            'h1',
            'h1.article-title',
            'h1.headline',
            '.article-title',
            '.headline',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                return title_elem.get_text().strip()
        
        return ""
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content from the page."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try different selectors for main content
        content_selectors = [
            'article',
            '.article-content',
            '.article-body',
            '.content',
            '.post-content',
            '.entry-content',
            'main',
            '[role="main"]'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Get all paragraphs within the content area
                paragraphs = content_elem.find_all(['p', 'h2', 'h3', 'h4'])
                if paragraphs:
                    content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if len(content) > 100:  # Ensure we have substantial content
                        return content
        
        # Fallback: get all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            return content
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """Extract article summary/description."""
        summary_selectors = [
            '.summary',
            '.description',
            '.excerpt',
            'meta[name="description"]',
            'meta[property="og:description"]'
        ]
        
        for selector in summary_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    return elem.get('content', '')
                else:
                    return elem.get_text().strip()
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author."""
        author_selectors = [
            '.author',
            '.byline',
            '[rel="author"]',
            'meta[name="author"]',
            'meta[property="article:author"]'
        ]
        
        for selector in author_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    return elem.get('content', '')
                else:
                    return elem.get_text().strip()
        
        return ""
    
    def _extract_published_date(self, soup: BeautifulSoup) -> str:
        """Extract article publication date."""
        date_selectors = [
            '.published-date',
            '.date',
            'time',
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    return elem.get('content', '')
                else:
                    return elem.get_text().strip()
        
        return ""
    
    def extract_multiple_articles(self, urls: List[str], delay: float = 1.0) -> List[Dict[str, str]]:
        """
        Extract content from multiple URLs with a delay between requests.
        
        Args:
            urls (List[str]): List of URLs to extract content from
            delay (float): Delay between requests in seconds
            
        Returns:
            List[Dict[str, str]]: List of extracted content dictionaries
        """
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"Processing article {i+1}/{len(urls)}: {url}")
            
            result = self.extract_article_content(url)
            results.append(result)
            
            # Add delay between requests to be respectful to servers
            if i < len(urls) - 1:  # Don't delay after the last request
                time.sleep(delay)
        
        return results

# Convenience function for single article extraction
def extract_article_content(url: str) -> Dict[str, str]:
    """
    Convenience function to extract content from a single article URL.
    
    Args:
        url (str): The URL of the article to extract content from
        
    Returns:
        Dict[str, str]: Dictionary containing extracted content
    """
    extractor = ArticleExtractor()
    return extractor.extract_article_content(url)

# Convenience function for multiple article extraction
def extract_multiple_articles(urls: List[str], delay: float = 1.0) -> List[Dict[str, str]]:
    """
    Convenience function to extract content from multiple article URLs.
    
    Args:
        urls (List[str]): List of URLs to extract content from
        delay (float): Delay between requests in seconds
        
    Returns:
        List[Dict[str, str]]: List of extracted content dictionaries
    """
    extractor = ArticleExtractor()
    return extractor.extract_multiple_articles(urls, delay) 