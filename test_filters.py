#!/usr/bin/env python3
"""
Test the filtering logic to make sure it works correctly
"""

import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fakenewsnet')

def test_viral_content_filter():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("=== TESTING VIRAL CONTENT FILTERS ===\n")
    
    # Test 1: Last 1 hour
    hours = 1
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    cur.execute("""
        SELECT 
            na.article_id,
            na.title,
            COUNT(t.tweet_id) as tweet_count,
            COALESCE(SUM(t.retweet_count), 0) as total_retweets
        FROM news_article na
        JOIN tweet t ON na.article_id = t.article_id
        WHERE t.created_at >= %s
        GROUP BY na.article_id, na.title
        ORDER BY total_retweets DESC
        LIMIT 5
    """, (time_threshold,))
    
    print(f"Viral content - Last {hours} hour(s):")
    results = cur.fetchall()
    for article_id, title, tweets, retweets in results:
        print(f"  {article_id}: {retweets} retweets, {tweets} tweets")
    print(f"Total articles with tweets in last {hours}h: {len(results)}")
    
    # Test 2: Last 24 hours  
    hours = 24
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    cur.execute("""
        SELECT 
            na.article_id,
            na.title,
            COUNT(t.tweet_id) as tweet_count,
            COALESCE(SUM(t.retweet_count), 0) as total_retweets
        FROM news_article na
        JOIN tweet t ON na.article_id = t.article_id
        WHERE t.created_at >= %s
        GROUP BY na.article_id, na.title
        ORDER BY total_retweets DESC
        LIMIT 5
    """, (time_threshold,))
    
    print(f"\nViral content - Last {hours} hour(s):")
    results = cur.fetchall()
    for article_id, title, tweets, retweets in results:
        print(f"  {article_id}: {retweets} retweets, {tweets} tweets")
    print(f"Total articles with tweets in last {hours}h: {len(results)}")
    
    # Test 3: Filter by fake news only
    print(f"\nViral FAKE news - Last 24 hours:")
    cur.execute("""
        SELECT 
            na.article_id,
            na.title,
            na.label,
            COUNT(t.tweet_id) as tweet_count,
            COALESCE(SUM(t.retweet_count), 0) as total_retweets
        FROM news_article na
        JOIN tweet t ON na.article_id = t.article_id
        WHERE t.created_at >= %s AND na.label = 'fake'
        GROUP BY na.article_id, na.title, na.label
        ORDER BY total_retweets DESC
        LIMIT 5
    """, (datetime.utcnow() - timedelta(hours=24),))
    
    results = cur.fetchall()
    for article_id, title, label, tweets, retweets in results:
        print(f"  {article_id}: {retweets} retweets, {tweets} tweets ({label})")
    
    # Test 4: Filter by real news only
    print(f"\nViral REAL news - Last 24 hours:")
    cur.execute("""
        SELECT 
            na.article_id,
            na.title,
            na.label,
            COUNT(t.tweet_id) as tweet_count,
            COALESCE(SUM(t.retweet_count), 0) as total_retweets
        FROM news_article na
        JOIN tweet t ON na.article_id = t.article_id
        WHERE t.created_at >= %s AND na.label = 'real'
        GROUP BY na.article_id, na.title, na.label
        ORDER BY total_retweets DESC
        LIMIT 5
    """, (datetime.utcnow() - timedelta(hours=24),))
    
    results = cur.fetchall()
    for article_id, title, label, tweets, retweets in results:
        print(f"  {article_id}: {retweets} retweets, {tweets} tweets ({label})")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    test_viral_content_filter()