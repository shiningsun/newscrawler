"""
Network utilities for handling connection issues and asyncio warnings
"""

import asyncio
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def setup_asyncio_exception_handling():
    """Setup asyncio exception handling to suppress common network warnings"""
    if sys.platform == "win32":
        def handle_connection_reset(loop, context):
            exception = context.get('exception')
            if isinstance(exception, ConnectionResetError):
                # Suppress ConnectionResetError warnings - these are common on Windows
                # when remote servers close connections unexpectedly
                return
            elif isinstance(exception, ConnectionAbortedError):
                # Suppress ConnectionAbortedError warnings
                return
            elif isinstance(exception, BrokenPipeError):
                # Suppress BrokenPipeError warnings
                return
            else:
                # Let other exceptions be handled normally
                loop.default_exception_handler(context)
        
        try:
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(handle_connection_reset)
            logger.debug("Configured asyncio exception handler for Windows")
        except RuntimeError:
            # No running event loop, will be set up when the app starts
            pass

def create_robust_session():
    """Create a requests session with robust error handling"""
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    session = requests.Session()
    
    # Configure retry strategy with more robust error handling
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1,
        raise_on_status=False  # Don't raise exceptions on status codes
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def handle_network_errors(func):
    """Decorator to handle common network errors gracefully"""
    import functools
    import requests
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error in {func.__name__}: {e}")
            return None
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout error in {func.__name__}: {e}")
            return None
        except ConnectionResetError as e:
            logger.debug(f"Connection reset in {func.__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return None
    
    return wrapper 