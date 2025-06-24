# API Configuration Template
# Copy this file to config.py and add your actual API keys

# TheNewsAPI Configuration
# Get your API key from: https://thenewsapi.com/
THENEWSAPI_TOKEN = "YOUR_THENEWSAPI_TOKEN_HERE"

# GNews API Configuration
# Get your API key from: https://gnews.io/
GNEWS_API_KEY = "YOUR_GNEWS_API_KEY_HERE"

# NYTimes API Configuration
# Get your API key from: https://developer.nytimes.com/
NYTIMES_API_KEY = "YOUR_NYTIMES_API_KEY_HERE"

# Guardian API Configuration
GUARDIAN_API_KEY = "your_guardian_api_key_here"  # <-- Add your Guardian API key here

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000

# Example: "postgresql+asyncpg://user:password@host:port/dbname"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/news_db")

# --- Domain Exclusion ---
# List of domains to exclude from crawling and processing.
# Subdomains will also be excluded (e.g., 'youtube.com' will also exclude 'music.youtube.com').
EXCLUDED_DOMAINS = [
    "youtube.com",
    "twitter.com",
    "facebook.com",
    "instagram.com",
    "reddit.com",
] 