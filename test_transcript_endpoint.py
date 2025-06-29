#!/usr/bin/env python3
"""
Test script for the /transcript endpoint
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_transcript_endpoint():
    """Test the /transcript endpoint with sample data"""
    
    # Sample transcript data with YouTube URL
    transcript_data = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "content": "This is a sample transcript content for a YouTube video..."
    }
    
    print("Testing /transcript endpoint with YouTube URL...")
    print(f"Request data: {json.dumps(transcript_data, indent=2)}")
    
    try:
        # Make POST request to /transcript endpoint
        response = requests.post(
            f"{BASE_URL}/transcript",
            json=transcript_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {json.dumps(result, indent=2)}")
            
            # Show extracted YouTube metadata
            if "youtube_metadata" in result:
                print("\nExtracted YouTube metadata:")
                metadata = result["youtube_metadata"]
                print(f"  Title: {result.get('title', 'N/A')}")
                print(f"  Author: {result.get('author', 'N/A')}")
                print(f"  Published Date: {result.get('published_date', 'N/A')}")
                print(f"  View Count: {metadata.get('view_count', 'N/A')}")
                print(f"  Like Count: {metadata.get('like_count', 'N/A')}")
                print(f"  Error: {metadata.get('error', 'None')}")
        else:
            print(f"Error! Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

def test_transcript_without_title():
    """Test creating a transcript without a title (should work)"""
    
    # Sample transcript data without title (YouTube URL)
    transcript_data = {
        "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
        "content": "This is a transcript without a title but with required content..."
    }
    
    print("\nTesting /transcript endpoint with YouTube URL (no title expected)...")
    print(f"Request data: {json.dumps(transcript_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/transcript",
            json=transcript_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error! Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

def test_transcript_without_content():
    """Test creating a transcript without content (should fail)"""
    
    # Sample transcript data without content
    transcript_data = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        # Missing content - will return 422 validation error
    }
    
    print("\nTesting /transcript endpoint without content (should fail)...")
    print(f"Request data: {json.dumps(transcript_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/transcript",
            json=transcript_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 422:  # Validation error
            print("✓ Correctly rejected - content is required")
            result = response.json()
            print(f"Validation error: {json.dumps(result, indent=2)}")
        else:
            print(f"Unexpected response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

def test_get_transcripts():
    """Test the GET /transcripts endpoint"""
    
    print("\nTesting GET /transcripts endpoint...")
    
    try:
        # Test basic retrieval
        response = requests.get(f"{BASE_URL}/transcripts")
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Found {result.get('transcripts_found', 0)} transcripts")
            print(f"Total results: {result.get('total_results', 0)}")
            
            # Show first few transcripts if any
            transcripts = result.get('transcripts', [])
            if transcripts:
                print("\nFirst transcript:")
                first = transcripts[0]
                print(f"  Title: {first.get('title', 'N/A')}")
                print(f"  URL: {first.get('url', 'N/A')}")
                print(f"  Category: {first.get('category', 'N/A')}")
                print(f"  Domain: {first.get('domain', 'N/A')}")
        else:
            print(f"Error! Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

def test_transcript_upsert():
    """Test upsert functionality by posting the same URL twice"""
    
    transcript_data = {
        "url": "https://www.youtube.com/watch?v=oHg5SJYRHA0",
        "content": "This is the first version of the transcript..."
    }
    
    print("\nTesting upsert functionality with YouTube URL...")
    print("First POST (should create):")
    
    try:
        response1 = requests.post(
            f"{BASE_URL}/transcript",
            json=transcript_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"First response: {response1.status_code}")
        if response1.status_code == 200:
            print(f"First result: {response1.json()}")
        
        # Update the content and post again
        transcript_data["content"] = "This is the updated version of the transcript..."
        
        print("\nSecond POST (should update):")
        response2 = requests.post(
            f"{BASE_URL}/transcript",
            json=transcript_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Second response: {response2.status_code}")
        if response2.status_code == 200:
            print(f"Second result: {response2.json()}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Transcript Endpoint Test ===\n")
    
    # Test basic functionality
    test_transcript_endpoint()
    
    # Test get transcripts
    test_get_transcripts()
    
    # Test upsert functionality
    test_transcript_upsert()
    
    # Test creating a transcript without a title
    test_transcript_without_title()
    
    # Test creating a transcript without content
    test_transcript_without_content()
    
    print("\n=== Test Complete ===") 