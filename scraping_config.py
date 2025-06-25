# Scraping Configuration
# Modify these settings to adjust scraping behavior

SCRAPING_CONFIG = {
    # Timing settings
    'min_delay': 1.0,           # Minimum delay between requests (seconds)
    'max_delay': 3.0,           # Maximum delay between requests (seconds)
    'domain_rate_limit': 2.0,   # Minimum interval between requests to same domain (seconds)
    
    # Request settings
    'timeout': 20,              # Request timeout (seconds)
    'max_retries': 3,           # Maximum retries for failed requests
    
    # Error handling delays
    '403_retry_delay': (5.0, 10.0),  # Delay range after 403 error (seconds)
    '429_retry_delay': (10.0, 20.0), # Delay range after 429 error (seconds)
    
    # Content extraction settings
    'min_content_length': 200,  # Minimum content length to consider valid
    'min_paragraph_length': 50, # Minimum paragraph length to include
}

# Anti-detection settings
ANTI_DETECTION_CONFIG = {
    'use_random_delays': True,      # Add random delays between requests
    'use_domain_rate_limiting': True,  # Rate limit requests per domain
    'use_realistic_headers': True,     # Use realistic browser headers
    'use_retry_logic': True,          # Retry failed requests
    'use_session_pooling': True,      # Reuse sessions for efficiency
}

# User agents (keep these updated)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
]

# Referrers for realistic requests
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

# Troubleshooting tips for 403 errors:
"""
If you're still getting 403 errors, try these adjustments:

1. Increase delays:
   - Set 'min_delay' to 3.0 and 'max_delay' to 6.0
   - Set 'domain_rate_limit' to 5.0

2. Add more user agents:
   - Update USER_AGENTS with newer browser versions
   - Add mobile user agents

3. Use proxies (advanced):
   - Implement proxy rotation in the extractor
   - Use residential proxies

4. Reduce concurrent requests:
   - Lower the semaphore limit in main.py
   - Process articles sequentially instead of concurrently

5. Check if the site has specific requirements:
   - Some sites require JavaScript
   - Some sites have geographic restrictions
   - Some sites require authentication
""" 