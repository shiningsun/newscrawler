#!/usr/bin/env python3
"""
Test script for the improved article extractor
"""

import asyncio
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.article_extractor import extract_article_content, SCRAPING_CONFIG

def test_extractor():
    """Test the article extractor with some URLs"""
    
    # Test URLs (including some that might give 403 errors)
    test_urls = [
        "https://www.thehill.com/homenews/house/5366846-house-al-green-trump-impeachment/",
        "https://www.politico.com/live-updates/2025/06/24/congress/most-democrats-vote-to-kill-impeachment-measure-00421254",
        "https://www.nytimes.com/2025/06/24/us/politics/democrats-congress-oversight-post.html",
        "https://www.washingtonpost.com/politics/2025/06/24/democrats-oversight-committee-garcia/",
    ]
    
    print("Testing improved article extractor...")
    print(f"Configuration: {SCRAPING_CONFIG}")
    print("=" * 60)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{i}. Testing: {url}")
        print("-" * 40)
        
        try:
            result = extract_article_content(url)
            
            if result['error']:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Success!")
                print(f"   Title: {result['title'][:100]}...")
                print(f"   Content length: {len(result['content'])} characters")
                print(f"   Author: {result['author']}")
                print(f"   Final URL: {result['url']}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print()

if __name__ == "__main__":
    test_extractor() 