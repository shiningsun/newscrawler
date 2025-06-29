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
    
    # Test valid YouTube URLs
    test_youtube_extractor()
    
    # Test invalid URLs
    test_invalid_url()
    
    print("=== Test Complete ===") 