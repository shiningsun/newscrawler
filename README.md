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
python scripts/setup_database.py
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

## Database Schema Fixes

- **Schema Migration:**  
  The database schema has been updated to ensure all text fields (such as `description`, `content`, `summary`, and `extraction_error`) use the `TEXT` type, and all `VARCHAR` columns have been extended to large sizes to prevent truncation errors.
- **One-off Fix Scripts Removed:**  
  Temporary schema fix scripts (`fix_database_schema.py`, `fix_db_schema_simple.py`, `fix_db_schema_final.py`, `force_fix_db_schema.py`) were used to correct legacy schema issues.  
  **These scripts have now been deleted** after confirming the schema is correct and stable.
- **Best Practice:**  
  For future schema changes, use a migration tool such as [Alembic](https://alembic.sqlalchemy.org/) to manage database migrations in a robust and versioned way.

> **Note:**
> If you encounter schema-related errors (e.g., string truncation), ensure your database schema matches the SQLAlchemy model definitions in `database.py`.  
> If you need to reapply schema fixes, refer to your version control history or use a migration tool.

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

### 5. Search Articles
```
GET /search
```

**Parameters:**
- `q`: Search query (keywords to search for in article titles, descriptions, content, and author)
- `limit`: Maximum number of articles to return (default: 20)
- `offset`: Number of articles to skip for pagination (default: 0)

**Behavior:**
- Returns articles that contain the search query (case-insensitive) in the title, description, content, or author fields.
- Only articles with content length of at least 800 characters are considered.
- Results are ordered by most recent `published_at`.

**Example:**
```bash
curl "http://localhost:8000/search?q=AI&limit=10&offset=0"
```

### 6. Get Headlines
```
GET /headlines
```

#### Description
Returns the top news headlines from Google News, grouped by clusters as they appear on the "Top stories" page. Each group corresponds to a cluster of related stories (as grouped by Google News), and each group contains a list of headline titles.

#### Query Parameters
- `language` (string, default: "en"): Language code for the news (e.g., "en", "es").
- `limit` (integer, default: 10): Maximum number of headline groups (clusters) to return.

#### Response
- `status`: "success" if the request was successful.
- `language`: The language code used.
- `limit`: The number of headline groups requested.
- `headlines_group_count`: The number of headline groups returned.
- `headlines_total_count`: The total number of headlines (sum of all groups).
- `headlines_grouped`: A list of lists, where each sublist contains the titles of related stories in a group.

#### Example Response
```json
{
  "status": "success",
  "language": "en",
  "limit": 10,
  "headlines_group_count": 10,
  "headlines_total_count": 32,
  "headlines_grouped": [
    [
      "Biden, Trump face off in first 2024 debate",
      "Fact-checking the presidential debate"
    ],
    [
      "Supreme Court rules on major abortion case"
    ],
    ...
  ]
}
```

#### Example Usage
```
GET /headlines?language=en&limit=5
```
Returns the first 5 headline groups in English.

## Scripts Directory

The `scripts/` directory contains utility scripts for managing and testing the application:

### Database Management
- `db_manage.py` - Interactive database management utility
- `setup_database.py` - Initialize database tables
- `add_domain_column.py` - Add domain column to articles table
- `populate_domains.py` - Populate domain column for existing articles
- `remove_excluded_domains.py` - Remove articles from excluded domains
- `force_fix_db_schema.py` - Force fix database schema issues

### Testing Scripts
- `test_logging.py` - Test logging configuration
- `test_extractor.py` - Test article content extraction
- `test_db_connection.py` - Test database connectivity

### Usage
All scripts are designed to be run from the project root directory:
```bash
python scripts/db_manage.py
python scripts/test_logging.py
python scripts/setup_database.py
```

For detailed documentation, see `scripts/README.md`.

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

## Development

### Project Structure
```
newsCrawler/
├── main.py                 # FastAPI application entry point
├── database.py            # SQLAlchemy database configuration
├── logging_config.py      # Logging configuration
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker services configuration
├── Dockerfile            # Application container
├── scripts/              # Utility scripts
│   ├── db_manage.py      # Database management utilities
│   ├── setup_database.py # Database setup script
│   ├── test_*.py         # Testing scripts
│   └── README.md         # Scripts documentation
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
   - Run `python scripts/setup_database.py` to create tables

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