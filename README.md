# News Crawler Service

A Python news crawler service using FastAPI that fetches news from multiple APIs (TheNewsAPI, GNews, NYTimes, Guardian) and extracts article content, storing data in PostgreSQL database.

## Features

- **Multiple News Sources**: Fetch news from TheNewsAPI, GNews, NYTimes, and Guardian APIs
- **Google News Crawler**: Web scraping of Google News with category filtering and content extraction
- **Content Extraction**: Extract full article content from URLs using web scraping
- **SQL Database**: Store articles in PostgreSQL with proper indexing and relationships
- **Caching**: Cache extracted content to avoid repeated web scraping
- **Filtering**: Filter articles by categories, language, search terms, domains, date, and sources
- **RESTful API**: Clean FastAPI endpoints with automatic documentation

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker and Docker Compose (optional)

## Installation

### Option 1: Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd newsCrawler
```

2. Create a `.env` file with your API keys:
```bash
THENEWSAPI_TOKEN=your_thenewsapi_token
GNEWS_API_KEY=your_gnews_api_key
NYTIMES_API_KEY=your_nytimes_api_key
```

3. Start the services:
```bash
docker-compose up -d
```

The application will be available at `http://localhost:8000`

### Option 2: Local Development

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database:
```bash
# Create database
createdb news_db

# Or using psql
psql -U postgres
CREATE DATABASE news_db;
```

3. Set environment variables:
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/news_db"
export THENEWSAPI_TOKEN="your_thenewsapi_token"
export GNEWS_API_KEY="your_gnews_api_key"
export NYTIMES_API_KEY="your_nytimes_api_key"
```

4. Set up database tables:
```bash
python setup_database.py
```

5. Run the application:
```bash
python main.py
```

## Database Schema

The application uses PostgreSQL with the following main table:

### Articles Table
- `id`: Primary key (auto-increment)
- `url`: Unique URL identifier
- `title`: Article title
- `description`: Article description
- `content`: Full article content (extracted)
- `summary`: Article summary
- `author`: Article author
- `image_url`: Featured image URL
- `language`: Article language code
- `published_at`: Publication date
- `source`: News source name
- `source_api`: API source identifier
- `categories`: JSON array of categories
- `extraction_error`: Error message if extraction failed
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

## API Endpoints

### 1. Get News Articles
```
GET /news
```

**Parameters:**
- `categories`: Comma-separated list of categories
- `language`: Language code (default: "en")
- `search`: Search term to filter articles
- `domains`: Comma-separated list of domains
- `published_after`: Filter articles published after date (YYYY-MM-DD)
- `extract`: Extract article content (default: true)
- `sources`: Comma-separated list of sources (thenewsapi,gnews,nytimes,guardian)
- `limit`: Maximum number of articles (default: 10)

**Example:**
```bash
curl "http://localhost:8000/news?categories=technology&language=en&limit=5"
```

### 2. Extract Single Article
```
GET /extract-article
```

**Parameters:**
- `url`: URL of the article to extract
- `force_extract`: Force extraction from web (default: false)

**Example:**
```bash
curl "http://localhost:8000/extract-article?url=https://example.com/article"
```

### 3. Extract Multiple Articles
```
GET /extract-articles
```

**Parameters:**
- `limit`: Number of articles to extract (default: 5)
- `delay`: Delay between requests in seconds (default: 1.0)
- `force_extract`: Force extraction from web (default: false)

**Example:**
```bash
curl "http://localhost:8000/extract-articles?limit=3&delay=2.0"
```

### 4. Crawl Google News
```
POST /crawlnews
```

**Parameters:**
- `categories`: Comma-separated list of Google News categories
- `language`: Language code (default: "en")
- `search`: Keyword(s) to filter articles
- `limit`: Maximum number of articles (default: 10)

**Example:**
```bash
curl -X POST "http://localhost:8000/crawlnews?categories=technology,world&search=AI&limit=5"
```

## Google News Crawler

The Google News crawler provides:
- Dynamic category discovery from Google News homepage
- Content extraction from publisher URLs
- URL decoding using `google-news-url-decoder`
- Anti-blocking measures (user-agent rotation, delays)
- Content filtering (minimum 1000 characters)
- Search keyword filtering

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `THENEWSAPI_TOKEN`: TheNewsAPI authentication token
- `GNEWS_API_KEY`: GNews API key
- `NYTIMES_API_KEY`: NYTimes API key

### Database Configuration
The application automatically creates tables on startup. For production, consider using Alembic for database migrations.

## Database Management

### Setup Database
```bash
python setup_database.py
```

### Database Management Tool
```bash
python db_manage.py
```

The database management tool provides:
- Show database statistics
- View recent articles
- Search articles by title or content
- Cleanup old articles
- Reset database

## Development

### Project Structure
```
newsCrawler/
├── main.py                 # FastAPI application entry point
├── database.py            # SQLAlchemy database configuration
├── setup_database.py      # Database setup script
├── db_manage.py          # Database management utilities
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker services configuration
├── Dockerfile            # Application container
├── services/
│   ├── news_service.py   # News service business logic
│   └── apis/
│       ├── news_sources.py      # API integrations
│       └── google_news_crawler.py # Google News scraper
└── utils/
    └── article_extractor.py     # Content extraction utilities
```

### Adding New News Sources
1. Add the source to `services/apis/news_sources.py`
2. Update the `source_strategies` mapping in `NewsService`
3. Add any required API keys to environment variables

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL format
   - Verify database exists
   - Run `python setup_database.py` to create tables

2. **Google News Crawling Issues**
   - Google may block requests if too frequent
   - Check user-agent rotation and delays
   - Verify URL decoder is working

3. **Content Extraction Failures**
   - Some websites block scraping
   - Check extraction_error field for details
   - Try force_extract=true to bypass cache

4. **Missing Dependencies**
   - Run `pip install -r requirements.txt`
   - Ensure all SQLAlchemy dependencies are installed

## API Documentation

Once the service is running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## License

This project is licensed under the MIT License. 