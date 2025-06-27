#!/usr/bin/env python3
"""
Quick script to check what data we have in the database
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fakenewsnet')

def check_database():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("=== DATABASE STATUS CHECK ===\n")
        
        # Check sources
        cur.execute("SELECT source_name, COUNT(*) FROM news_article na JOIN news_source ns ON na.source_id = ns.source_id GROUP BY source_name ORDER BY COUNT(*) DESC")
        sources = cur.fetchall()
        print("Articles by Source:")
        for source, count in sources:
            print(f"  {source}: {count} articles")
        
        # Check total articles
        cur.execute("SELECT COUNT(*) FROM news_article")
        total_articles = cur.fetchone()[0]
        print(f"\nTotal Articles: {total_articles}")
        
        # Check by label
        cur.execute("SELECT label, COUNT(*) FROM news_article GROUP BY label")
        labels = cur.fetchall()
        print("\nArticles by Label:")
        for label, count in labels:
            print(f"  {label}: {count} articles")
        
        # Check users
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        print(f"\nTotal Users: {total_users}")
        
        # Check tweets
        cur.execute("SELECT COUNT(*) FROM tweet")
        total_tweets = cur.fetchone()[0]
        print(f"Total Tweets: {total_tweets}")
        
        # Check retweets
        cur.execute("SELECT COUNT(*) FROM retweet")
        total_retweets = cur.fetchone()[0]
        print(f"Total Retweets: {total_retweets}")
        
        # Check recent articles with tweets
        cur.execute("""
            SELECT na.article_id, na.title, na.label, COUNT(t.tweet_id) as tweet_count
            FROM news_article na
            LEFT JOIN tweet t ON na.article_id = t.article_id
            GROUP BY na.article_id, na.title, na.label
            ORDER BY tweet_count DESC
            LIMIT 10
        """)
        articles_with_tweets = cur.fetchall()
        print("\nTop 10 Articles with Most Tweets:")
        for article_id, title, label, tweet_count in articles_with_tweets:
            print(f"  {article_id}: {tweet_count} tweets - {title[:50]}... ({label})")
        
        # Check engagement scores
        cur.execute("""
            SELECT 
                na.article_id, 
                na.title, 
                COUNT(t.tweet_id) as tweets,
                COALESCE(SUM(t.retweet_count), 0) as total_retweets,
                COALESCE(SUM(t.favorite_count), 0) as total_favorites
            FROM news_article na
            LEFT JOIN tweet t ON na.article_id = t.article_id
            GROUP BY na.article_id, na.title
            HAVING COUNT(t.tweet_id) > 0
            ORDER BY total_retweets DESC
            LIMIT 5
        """)
        viral = cur.fetchall()
        print("\nTop 5 Most Retweeted Articles:")
        for article_id, title, tweets, retweets, favorites in viral:
            print(f"  {article_id}: {retweets} retweets, {favorites} favorites - {title[:40]}...")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database()