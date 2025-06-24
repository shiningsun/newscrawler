from urllib.parse import urlparse
import logging

try:
    from config import EXCLUDED_DOMAINS
except ImportError:
    # Default list if not defined in config
    EXCLUDED_DOMAINS = [
        "youtube.com",
        "twitter.com",
        "facebook.com",
        "instagram.com",
        "reddit.com",
    ]

logger = logging.getLogger(__name__)

def is_domain_excluded(url: str) -> bool:
    """
    Check if the domain of the URL is in the exclusion list.
    This check is case-insensitive and also checks for subdomains.
    """
    if not url:
        return False
    try:
        domain = urlparse(url).netloc.lower()
        # Remove 'www.' prefix for broader matching
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return any(domain == excluded_domain or domain.endswith(f".{excluded_domain}") for excluded_domain in EXCLUDED_DOMAINS)
    except Exception as e:
        logger.warning(f"Could not parse URL '{url}' to check domain: {e}")
        return False 