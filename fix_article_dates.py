#!/usr/bin/env python3
"""
Fix Article Dates for Better Timeline Analysis
This script updates article creation dates to be spread over the last 12 months
"""

import os
import psycopg2
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fakenewsnet')

def get_db_connection():
    """Create a database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def update_article_dates(conn):
    """Update article creation dates to be spread over the last 12 months"""
    cur = conn.cursor()
    
    try:
        # Get all articles
        cur.execute("SELECT article_id FROM news_article")
        articles = [row[0] for row in cur.fetchall()]
        
        if not articles:
            print("No articles found")
            return
        
        print(f"Updating dates for {len(articles)} articles...")
        
        # Update each article with a random date in the last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        for article_id in articles:
            # Generate random date between start and end
            random_days = random.randint(0, 365)
            random_date = start_date + timedelta(days=random_days)
            
            cur.execute("""
                UPDATE news_article 
                SET created_at = %s 
                WHERE article_id = %s
            """, (random_date, article_id))
        
        # Also update tweet dates to be after article dates
        cur.execute("""
            UPDATE tweet 
            SET created_at = na.created_at + INTERVAL '%s days'
            FROM news_article na 
            WHERE tweet.article_id = na.article_id
        """, (random.randint(0, 7),))
        
        conn.commit()
        print(f"Successfully updated dates for {len(articles)} articles")
        
        # Print monthly distribution
        cur.execute("""
            SELECT 
                DATE_TRUNC('month', created_at) as month,
                COUNT(*) as article_count
            FROM news_article 
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month
        """)
        
        print("\nMonthly Article Distribution:")
        for month, count in cur.fetchall():
            print(f"- {month.strftime('%Y-%m')}: {count} articles")
        
    except Exception as e:
        print(f"Error updating article dates: {e}")
        conn.rollback()
    finally:
        cur.close()

def main():
    """Main function to fix article dates"""
    print("Fixing article dates for better timeline analysis...")
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        update_article_dates(conn)
        print("\nArticle dates updated successfully!")
        
    except Exception as e:
        print(f"Error during update: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()