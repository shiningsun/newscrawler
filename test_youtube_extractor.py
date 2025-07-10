#!/usr/bin/env python3
"""
Test script for the YouTube extractor functionality
"""

import sys
import os

# Add the parent directory to the path so we can import from the main project
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.youtube_extractor import extract_youtube_metadata
import json
import requests
from bs4 import BeautifulSoup

def debug_youtube_structure():
    """Debug function to inspect YouTube page structure"""
    
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("=== Debugging YouTube Page Structure ===\n")
    
    try:
        # Make a simple request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Set encoding
        if response.encoding == 'ISO-8859-1':
            response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"Response encoding: {response.encoding}")
        print(f"Response status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        
        # Look for title-related elements
        print("\n--- Title Elements ---")
        title_elements = soup.find_all(['h1', 'title', 'yt-formatted-string'])
        for i, elem in enumerate(title_elements[:10]):  # Show first 10
            print(f"{i+1}. Tag: {elem.name}, Class: {elem.get('class', 'None')}, Text: {elem.get_text()[:100]}...")
        
        # Look for ytd-watch-metadata
        print("\n--- ytd-watch-metadata Elements ---")
        metadata_elements = soup.find_all('ytd-watch-metadata')
        for i, elem in enumerate(metadata_elements):
            print(f"{i+1}. ytd-watch-metadata found: {elem}")
        
        # Look for channel/author elements
        print("\n--- Channel/Author Elements ---")
        channel_elements = soup.find_all(['a', 'yt-formatted-string'], class_=lambda x: x and any(word in str(x).lower() for word in ['channel', 'owner', 'author']))
        for i, elem in enumerate(channel_elements[:5]):
            print(f"{i+1}. Tag: {elem.name}, Class: {elem.get('class', 'None')}, Text: {elem.get_text()[:50]}...")
        
        # Check for JSON data in script tags
        print("\n--- Script Tags with JSON ---")
        script_tags = soup.find_all('script')
        for i, script in enumerate(script_tags):
            if script.string and ('title' in script.string or 'author' in script.string):
                print(f"{i+1}. Script tag with title/author data found (length: {len(script.string)})")
                # Look for specific patterns
                if '"title"' in script.string:
                    print("   Contains 'title' pattern")
                if '"author"' in script.string:
                    print("   Contains 'author' pattern")
        
    except Exception as e:
        print(f"Debug error: {e}")

def test_youtube_extractor():
    """Test the YouTube extractor with various YouTube URLs"""
    
    # Test URLs (using well-known YouTube videos)
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll
        "https://www.youtube.com/watch?v=9bZkp7q19f0",  # PSY - GANGNAM STYLE
        "https://www.youtube.com/watch?v=oHg5SJYRHA0",  # Never Gonna Give You Up
    ]
    
    print("=== YouTube Extractor Test ===\n")
    
    for i, url in enumerate(test_urls, 1):
        print(f"Test {i}: {url}")
        print("-" * 50)
        
        try:
            # Extract metadata
            metadata = extract_youtube_metadata(url)
            
            # Display results
            print(f"Title: {metadata.get('title', 'N/A')}")
            print(f"Author: {metadata.get('author', 'N/A')}")
            print(f"Published Date: {metadata.get('published_date', 'N/A')}")
            print(f"Description: {metadata.get('description', 'N/A')[:100]}...")
            print(f"View Count: {metadata.get('view_count', 'N/A')}")
            print(f"Like Count: {metadata.get('like_count', 'N/A')}")
            print(f"Error: {metadata.get('error', 'None')}")
            
            if metadata.get('error'):
                print(f"⚠️  Extraction failed: {metadata['error']}")
            else:
                print("✅ Extraction successful")
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        
        print("\n")

def test_invalid_url():
    """Test with invalid URLs"""
    
    print("=== Invalid URL Test ===\n")
    
    invalid_urls = [
        "https://example.com/not-youtube",
        "https://youtube.com/invalid-path",
        "not-a-url",
        "https://www.youtube.com/playlist?list=PLbpi6ZahtOH6Bljwxs1dstq4mKskq3Ick",
    ]
    
    for i, url in enumerate(invalid_urls, 1):
        print(f"Test {i}: {url}")
        print("-" * 30)
        
        try:
            metadata = extract_youtube_metadata(url)
            
            if metadata.get('error') == 'Invalid YouTube URL':
                print("✅ Correctly identified as invalid YouTube URL")
            else:
                print(f"⚠️  Unexpected result: {metadata.get('error', 'No error')}")
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        
        print()

if __name__ == "__main__":
    print("Testing YouTube Metadata Extractor\n")
    
    # Debug the page structure first
    debug_youtube_structure()
    
    # Test valid YouTube URLs
    test_youtube_extractor()
    
    # Test invalid URLs
    test_invalid_url()
    
    print("=== Test Complete ===") 