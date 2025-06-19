# Python Service

A basic Python service built with FastAPI that fetches news from multiple APIs and extracts article content.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. **Configure API Keys**:
   - Copy `config_template.py` to `config.py`
   - Add your API keys to `config.py`:
     - Get TheNewsAPI key from: https://thenewsapi.com/
     - Get GNews API key from: https://gnews.io/
   - The `config.py` file is ignored by git to keep your API keys secure

## Running the Service

To start the service, run:
```bash
python main.py
```

The service will be available at `http://localhost:8000`

## API Endpoints

- `GET /`: Welcome message
- `GET /health`: Health check endpoint
- `GET /news`: Fetch news articles with optional parameters
- `GET /extract-article`: Extract content from a single article URL
- `GET /extract-articles`: Extract content from stored news articles
- `GET /docs`: Interactive API documentation (Swagger UI)
- `GET /redoc`: Alternative API documentation (ReDoc)

## News Endpoint Parameters

- `categories`: Comma-separated list of categories to filter by
- `language`: Language code (default: en)
- `search`: Search term to filter articles
- `domains`: Comma-separated list of domains to filter by
- `published_after`: Filter articles published after this date (YYYY-MM-DD format, default: yesterday)
- `extract`: Extract article content (default: true)
- `sources`: Comma-separated list of sources to use (`thenewsapi`, `gnews`, `nytimes`). Example: `sources=thenewsapi,gnews`. If omitted, all sources are used by default.

## Features

- **Multi-API Integration**: Fetches news from TheNewsAPI, GNews, and NYTimes
- **Source Toggling**: Select which APIs to use via the `sources` parameter
- **Content Extraction**: Automatically extracts full article content from URLs
- **Multiple Filters**: Search, categories, domains, language, and date filtering
- **Automatic API Documentation**: Swagger UI and ReDoc
- **CORS Support**: Cross-origin requests enabled
- **Error Handling**: Graceful handling of API failures
- **Rate Limiting**: Built-in delays to respect API limits
- **Modular API Logic**: Each news source is handled by a separate function for easy maintenance and extension

## Security

- API keys are stored in `config.py` which is ignored by git
- Never commit your actual API keys to version control
- Use the `config_template.py` as a reference for required configuration

## Example Usage

```bash
# Get all recent news from all sources
GET http://localhost:8000/news

# Only get news from TheNewsAPI and GNews
GET http://localhost:8000/news?sources=thenewsapi,gnews

# Only get news from NYTimes
GET http://localhost:8000/news?sources=nytimes

# Search for specific topics from all sources
GET http://localhost:8000/news?search=technology

# Filter by categories and domains
GET http://localhost:8000/news?categories=business&domains=bbc.com

# Get news from specific date range
GET http://localhost:8000/news?published_after=2025-06-01

# Disable content extraction for faster response
GET http://localhost:8000/news?extract=false
``` 