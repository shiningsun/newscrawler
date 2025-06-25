#!/usr/bin/env python3
"""
Force fix database schema - more aggressive approach to ensure all content columns are TEXT.
This script will drop and recreate columns if necessary to ensure proper data types.
"""

import asyncio
import asyncpg
import os
import json
import sys

# Add the project root to the path (parent directory of scripts)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import AsyncSessionLocal, Article

async def force_fix_database_schema():
    """Force fix the database schema by recreating columns if necessary"""
    
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/news_db")
    
    print("Starting FORCE database schema fix...")
    print(f"Database URL: {database_url}")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Check current column types
        print("\nChecking current column types...")
        rows = await conn.fetch("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'articles' 
            ORDER BY ordinal_position;
        """)
        
        print("Current column definitions:")
        for row in rows:
            col_name, data_type, max_length = row
            length_str = f"({max_length})" if max_length else ""
            print(f"  {col_name}: {data_type}{length_str}")
        
        # Force convert all content columns to TEXT using a more aggressive approach
        print("\nForce converting content columns to TEXT...")
        text_columns = ['description', 'content', 'summary', 'extraction_error']
        
        for column in text_columns:
            try:
                # First, check if the column is already TEXT
                row = await conn.fetchrow(f"""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'articles' AND column_name = $1;
                """, column)
                
                if row and row[0] == 'text':
                    print(f"  ✓ {column} is already TEXT")
                else:
                    print(f"Force converting {column} to TEXT...")
                    
                    # Use USING clause to force the conversion
                    await conn.execute(f"""
                        ALTER TABLE articles 
                        ALTER COLUMN {column} TYPE TEXT 
                        USING {column}::TEXT;
                    """)
                    print(f"  ✓ {column} converted to TEXT")
                    
            except Exception as e:
                print(f"  ✗ Error converting {column}: {e}")
                # Try alternative approach - drop and recreate column
                try:
                    print(f"  Trying alternative approach for {column}...")
                    await conn.execute(f"""
                        ALTER TABLE articles 
                        DROP COLUMN {column};
                    """)
                    await conn.execute(f"""
                        ALTER TABLE articles 
                        ADD COLUMN {column} TEXT;
                    """)
                    print(f"  ✓ {column} recreated as TEXT")
                except Exception as e2:
                    print(f"  ✗ Failed to recreate {column}: {e2}")
        
        # Extend all VARCHAR columns to very large sizes
        print("\nExtending VARCHAR columns to very large sizes...")
        varchar_fixes = [
            ('title', 5000),
            ('url', 5000),
            ('author', 2000),
            ('image_url', 5000),
            ('source', 1000),
            ('source_api', 500)
        ]
        
        for column, length in varchar_fixes:
            try:
                print(f"Extending {column} to VARCHAR({length})...")
                await conn.execute(f"ALTER TABLE articles ALTER COLUMN {column} TYPE VARCHAR({length});")
                print(f"  ✓ {column} extended to VARCHAR({length})")
            except Exception as e:
                print(f"  ✗ Error extending {column}: {e}")
        
        print("\nForce database schema fix completed!")
        
        # Verify the changes
        print("\nVerifying final column types...")
        rows = await conn.fetch("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'articles' 
            ORDER BY ordinal_position;
        """)
        
        print("Final column definitions:")
        for row in rows:
            col_name, data_type, max_length = row
            length_str = f"({max_length})" if max_length else ""
            print(f"  {col_name}: {data_type}{length_str}")
        
        # Test insert to verify the schema works
        print("\nTesting schema with a sample insert...")
        try:
            test_data = {
                'url': 'https://test.com/article',
                'title': 'Test Article Title',
                'description': 'A' * 2000,  # 2000 character description
                'content': 'B' * 5000,      # 5000 character content
                'summary': 'C' * 1000,      # 1000 character summary
                'author': 'Test Author',
                'image_url': 'https://test.com/image.jpg',
                'language': 'en',
                'source': 'Test Source',
                'source_api': 'test',
                'categories': json.dumps(['test'])  # Convert list to JSON string
            }
            
            await conn.execute("""
                INSERT INTO articles (url, title, description, content, summary, author, image_url, language, source, source_api, categories)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, test_data['url'], test_data['title'], test_data['description'], test_data['content'], 
                 test_data['summary'], test_data['author'], test_data['image_url'], test_data['language'],
                 test_data['source'], test_data['source_api'], test_data['categories'])
            
            print("  ✓ Test insert successful - schema is working!")
            
            # Clean up test data
            await conn.execute("DELETE FROM articles WHERE url = $1", test_data['url'])
            print("  ✓ Test data cleaned up")
            
        except Exception as e:
            print(f"  ✗ Test insert failed: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error during schema fix: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(force_fix_database_schema()) 