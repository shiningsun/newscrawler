# News Crawler Service

A comprehensive Python service built with FastAPI that fetches news from multiple APIs, extracts article content, and stores data in MongoDB for caching and persistence.

## Features

- **Multi-API Integration**: Fetches news from TheNewsAPI, GNews, NYTimes, and The Guardian
- **Content Extraction**: Automatically extracts full article content from URLs using web scraping
- **MongoDB Integration**: Stores articles and extracted content for caching and persistence
- **Source Toggling**: Select which APIs to use via the `sources` parameter
- **Advanced Filtering**: Search, categories, domains, language, and date filtering
- **Rate Limiting**: Built-in delays to respect API limits and be respectful to web servers
- **Error Handling**: Graceful handling of API failures and extraction errors
- **Automatic API Documentation**: Swagger UI and ReDoc
- **CORS Support**: Cross-origin requests enabled
- **Modular Architecture**: Each news source is handled by a separate function for easy maintenance

## Project Structure

```
newsCrawler/
├── main.py                 # FastAPI application entry point
├── config_template.py      # Configuration template
├── requirements.txt        # Python dependencies
├── services/
│   ├── news_service.py     # Main news service logic
│   └── apis/
│       └── news_sources.py # Individual API integrations
└── utils/
    └── article_extractor.py # Web scraping and content extraction
```

## Setup

### 1. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Copy `config_template.py` to `config.py` and add your API keys:

```python
# TheNewsAPI Configuration
THENEWSAPI_TOKEN = "YOUR_THENEWSAPI_TOKEN_HERE"

# GNews API Configuration  
GNEWS_API_KEY = "YOUR_GNEWS_API_KEY_HERE"

# NYTimes API Configuration
NYTIMES_API_KEY = "YOUR_NYTIMES_API_KEY_HERE"

# Guardian API Configuration
GUARDIAN_API_KEY = "YOUR_GUARDIAN_API_KEY_HERE"
```

**Get API Keys:**
- [TheNewsAPI](https://thenewsapi.com/)
- [GNews](https://gnews.io/)
- [NYTimes](https://developer.nytimes.com/)
- [The Guardian](https://open-platform.theguardian.com/)

### 4. MongoDB Setup (Optional)
The service uses MongoDB for caching and persistence. Set environment variables:
```bash
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB="news_db"
```

If MongoDB is not available, the service will still work but without caching.

## Running the Service

Start the service:
```bash
python main.py
```

The service will be available at `http://localhost:8000`

## API Endpoints

### Core Endpoints
- `GET /`: Welcome message
- `GET /health`: Health check endpoint
- `GET /docs`: Interactive API documentation (Swagger UI)
- `GET /redoc`: Alternative API documentation (ReDoc)

### News Endpoints
- `GET /news`: Fetch news articles with optional parameters
- `GET /extract-article`: Extract content from a single article URL
- `GET /extract-articles`: Extract content from stored news articles

## News Endpoint Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `categories` | string | None | Comma-separated list of categories to filter by |
| `language` | string | "en" | Language code |
| `search` | string | None | Search term to filter articles |
| `domains` | string | None | Comma-separated list of domains to filter by |
| `published_after` | string | yesterday | Filter articles published after this date (YYYY-MM-DD) |
| `extract` | boolean | true | Extract article content from URLs |
| `sources` | string | all | Comma-separated list of sources: `thenewsapi`, `gnews`, `nytimes`, `guardian` |
| `limit` | integer | 10 | Maximum number of articles per source |

## Example Usage

### Basic News Fetching
```bash
# Get all recent news from all sources
GET http://localhost:8000/news

# Get 5 articles from each source
GET http://localhost:8000/news?limit=5

# Search for specific topics
GET http://localhost:8000/news?search=artificial intelligence
GET http://localhost:8000/news?search=climate change,renewable energy
```

### Source Selection
```bash
# Only get news from specific sources
GET http://localhost:8000/news?sources=thenewsapi,gnews
GET http://localhost:8000/news?sources=nytimes,guardian&limit=3
```

### Advanced Filtering
```bash
# Filter by categories and domains
GET http://localhost:8000/news?categories=business,technology&domains=bbc.com,techcrunch.com

# Get news from specific date range
GET http://localhost:8000/news?published_after=2024-01-01

# Disable content extraction for faster response
GET http://localhost:8000/news?extract=false
```

### Content Extraction
```bash
# Extract content from a specific article
GET http://localhost:8000/extract-article?url=https://example.com/article

# Extract content from stored articles
GET http://localhost:8000/extract-articles?limit=5&delay=1.0
```

## Search Logic

### GNews Search Behavior
- Multiple search terms are joined with ' AND ' for precise results
- Examples:
  - `search=china,iran` → `q=china AND iran`
  - `search=climate change` → `q=climate AND change`

### Content Extraction Features
- **Automatic Caching**: Extracted content is stored in MongoDB
- **Force Extraction**: Use `force_extract=true` to bypass cache
- **Rate Limiting**: Built-in delays between requests (default: 1 second)
- **Error Handling**: Graceful handling of extraction failures

## Response Format

The `/news` endpoint returns:
```json
{
  "status": "success",
  "language": "en",
  "categories_filter": "business",
  "search_term": "technology",
  "domains_filter": "bbc.com",
  "published_after": "2024-01-01",
  "extract_content": true,
  "sources": ["thenewsapi", "gnews"],
  "meta": {
    "thenewsapi": {...},
    "gnews": {...}
  },
  "articles": [
    {
      "title": "Article Title",
      "description": "Article description",
      "url": "https://example.com/article",
      "source": "Source Name",
      "published_at": "2024-01-01T10:00:00Z",
      "content": "Extracted article content...",
      "summary": "Article summary...",
      "author": "Author Name",
      "categories": ["business", "technology"],
      "source_api": "thenewsapi"
    }
  ]
}
```

## Security Considerations

- API keys are stored in `config.py` which is ignored by git
- Never commit your actual API keys to version control
- Use the `config_template.py` as a reference for required configuration
- The service includes rate limiting to respect API limits

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **Requests**: HTTP library for API calls
- **BeautifulSoup4**: Web scraping for content extraction
- **Motor**: Async MongoDB driver
- **Pydantic**: Data validation using Python type annotations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License. 