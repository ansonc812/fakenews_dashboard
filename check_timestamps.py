#!/usr/bin/env python3
"""
Check the timestamp distribution in our data
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fakenewsnet')

def check_timestamps():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("=== TIMESTAMP ANALYSIS ===\n")
    
    # Check article timestamps
    cur.execute("""
        SELECT 
            MIN(created_at) as earliest,
            MAX(created_at) as latest,
            COUNT(*) as total
        FROM news_article
    """)
    result = cur.fetchone()
    print(f"Articles: {result[2]} total")
    print(f"  Earliest: {result[0]}")
    print(f"  Latest: {result[1]}")
    
    # Check tweet timestamps
    cur.execute("""
        SELECT 
            MIN(created_at) as earliest,
            MAX(created_at) as latest,
            COUNT(*) as total
        FROM tweet
    """)
    result = cur.fetchone()
    print(f"\nTweets: {result[2]} total")
    print(f"  Earliest: {result[0]}")
    print(f"  Latest: {result[1]}")
    
    # Check tweets by hour (last 24 hours)
    cur.execute("""
        SELECT 
            EXTRACT(hour FROM NOW() - created_at) as hours_ago,
            COUNT(*) as tweet_count
        FROM tweet
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY EXTRACT(hour FROM NOW() - created_at)
        ORDER BY hours_ago
    """)
    print(f"\nTweets by hours ago (last 24h):")
    for hours_ago, count in cur.fetchall():
        print(f"  {int(hours_ago)}h ago: {count} tweets")
    
    # Check viral content in last 24h
    cur.execute("""
        SELECT 
            na.article_id,
            LEFT(na.title, 50) as title,
            COUNT(t.tweet_id) as tweets,
            SUM(t.retweet_count) as total_retweets
        FROM news_article na
        JOIN tweet t ON na.article_id = t.article_id
        WHERE t.created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY na.article_id, na.title
        ORDER BY total_retweets DESC
        LIMIT 5
    """)
    print(f"\nTop viral content (last 24h):")
    for article_id, title, tweets, retweets in cur.fetchall():
        print(f"  {article_id}: {retweets} retweets, {tweets} tweets - {title}...")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_timestamps()