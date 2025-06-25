#!/usr/bin/env python3
"""
Database management script for the news crawler service
Provides utilities for database operations.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import AsyncSessionLocal, Article, create_tables, drop_tables
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from logging_config import setup_logging, get_logger

# Initialize logging
setup_logging(log_level="INFO", app_name="db_manage")
logger = get_logger(__name__)

async def show_stats():
    """Show database statistics"""
    async with AsyncSessionLocal() as session:
        # Total articles
        result = await session.execute(select(func.count(Article.id)))
        total_articles = result.scalar()
        
        # Articles by source
        result = await session.execute(
            select(Article.source_api, func.count(Article.id))
            .group_by(Article.source_api)
        )
        articles_by_source = result.fetchall()
        
        # Recent articles (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await session.execute(
            select(func.count(Article.id))
            .where(Article.created_at >= week_ago)
        )
        recent_articles = result.scalar()
        
        # Articles with content
        result = await session.execute(
            select(func.count(Article.id))
            .where(Article.content.isnot(None))
        )
        articles_with_content = result.scalar()
        
        print("Database Statistics")
        print("=" * 30)
        print(f"Total articles: {total_articles}")
        print(f"Articles with content: {articles_with_content}")
        print(f"Recent articles (7 days): {recent_articles}")
        print("\nArticles by source:")
        for source, count in articles_by_source:
            print(f"  {source}: {count}")

async def cleanup_old_articles(days: int = 30):
    """Remove articles older than specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    async with AsyncSessionLocal() as session:
        # Count articles to be deleted
        result = await session.execute(
            select(func.count(Article.id))
            .where(Article.created_at < cutoff_date)
        )
        count_to_delete = result.scalar()
        
        if count_to_delete == 0:
            print(f"No articles older than {days} days found.")
            return
        
        # Confirm deletion
        response = input(f"Delete {count_to_delete} articles older than {days} days? (y/N): ")
        if response.lower() != 'y':
            print("Cleanup cancelled.")
            return
        
        # Delete old articles
        await session.execute(
            delete(Article).where(Article.created_at < cutoff_date)
        )
        await session.commit()
        
        print(f"Deleted {count_to_delete} old articles.")

async def show_recent_articles(limit: int = 10):
    """Show recent articles"""
    try:
        async with AsyncSessionLocal() as session:
            # Use a more efficient query with pagination for large limits
            if limit > 100:
                print(f"Fetching {limit} articles (this may take a moment)...")
            
            # Add timeout for large queries
            if limit > 500:
                print("Large query detected. Adding timeout...")
                import asyncio
                try:
                    result = await asyncio.wait_for(
                        session.execute(
                            select(Article)
                            .order_by(Article.created_at.desc())
                            .limit(limit)
                        ),
                        timeout=30.0  # 30 second timeout
                    )
                except asyncio.TimeoutError:
                    print("Query timed out. Try reducing the number of articles.")
                    return
            else:
                result = await session.execute(
                    select(Article)
                    .order_by(Article.created_at.desc())
                    .limit(limit)
                )
            
            articles = result.scalars().all()
            
            print(f"Recent Articles (last {len(articles)})")
            print("=" * 40)
            
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article.title}")
                print(f"   Source: {article.source} ({article.source_api})")
                print(f"   URL: {article.url}")
                print(f"   Created: {article.created_at}")
                print(f"   Has content: {'Yes' if article.content else 'No'}")
                print()
                
                # Add pagination for large result sets
                if i % 50 == 0 and i < len(articles):
                    response = input("Press Enter to continue, 'q' to quit: ")
                    if response.lower() == 'q':
                        break
    except Exception as e:
        print(f"Error fetching articles: {e}")
        print("Try reducing the number of articles or check your database connection.")

async def search_articles(query: str, limit: int = 10):
    """Search articles by title or content"""
    async with AsyncSessionLocal() as session:
        # Search in title and content
        result = await session.execute(
            select(Article)
            .where(
                Article.title.ilike(f"%{query}%") |
                Article.content.ilike(f"%{query}%")
            )
            .order_by(Article.created_at.desc())
            .limit(limit)
        )
        articles = result.scalars().all()
        
        print(f"Search Results for '{query}'")
        print("=" * 40)
        
        if not articles:
            print("No articles found.")
            return
        
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   URL: {article.url}")
            print(f"   Created: {article.created_at}")
            print()

async def reset_database():
    """Reset the database (drop and recreate tables)"""
    response = input("This will delete ALL data. Are you sure? (y/N): ")
    if response.lower() != 'y':
        print("Reset cancelled.")
        return
    
    await drop_tables()
    await create_tables()
    print("Database reset successfully.")

def main():
    """Main function"""
    print("News Crawler Database Management")
    print("=" * 40)
    print("1. Show database statistics")
    print("2. Show recent articles")
    print("3. Search articles")
    print("4. Cleanup old articles")
    print("5. Reset database")
    print("6. Exit")
    
    # Create a single event loop for the entire session
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            choice = input("\nSelect option (1-6): ").strip()
            
            try:
                if choice == '1':
                    loop.run_until_complete(show_stats())
                elif choice == '2':
                    limit = input("Number of articles to show (default 10): ").strip()
                    limit = int(limit) if limit.isdigit() else 10
                    loop.run_until_complete(show_recent_articles(limit))
                elif choice == '3':
                    query = input("Search query: ").strip()
                    if query:
                        limit = input("Number of results (default 10): ").strip()
                        limit = int(limit) if limit.isdigit() else 10
                        loop.run_until_complete(search_articles(query, limit))
                    else:
                        print("Please enter a search query.")
                elif choice == '4':
                    days = input("Delete articles older than (days, default 30): ").strip()
                    days = int(days) if days.isdigit() else 30
                    loop.run_until_complete(cleanup_old_articles(days))
                elif choice == '5':
                    loop.run_until_complete(reset_database())
                elif choice == '6':
                    print("Goodbye!")
                    break
                else:
                    print("Invalid option. Please select 1-6.")
            except Exception as e:
                print(f"Error: {e}")
                print("Please try again.")
    
    finally:
        # Clean up the event loop
        try:
            # Cancel any pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            # Wait for tasks to be cancelled
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            loop.close()
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

if __name__ == "__main__":
    main() 