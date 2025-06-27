#!/usr/bin/env python3
"""
Data Import Script for FakeNewsNet Database
This script imports CSV data from Capstone Project 1 into the PostgreSQL database
"""

import os
import sys
import csv
import json
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fakenewsnet')

# Path to the data files
DATA_PATH = "/home/ansonc812/Documents/git/repos/fakenews_dashboard/project 1+2 deliverables/fakenewsnet/FakeNewsNet-master/dataset"

def get_db_connection():
    """Create a database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def create_tables_if_not_exists(conn):
    """Create tables using the schema from Project 2"""
    schema_file = "/home/ansonc812/Documents/git/repos/fakenews_dashboard/project 1+2 deliverables/create_tables.sql"
    
    if os.path.exists(schema_file):
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cur = conn.cursor()
        try:
            cur.execute(schema_sql)
            conn.commit()
            print("Database schema created successfully")
        except Exception as e:
            print(f"Error creating schema: {e}")
            conn.rollback()
        finally:
            cur.close()
    else:
        print(f"Schema file not found: {schema_file}")

def insert_news_sources(conn):
    """Insert news sources"""
    cur = conn.cursor()
    
    sources = [
        ('gossipcop', 'https://gossipcop.com', 0.85),
        ('politifact', 'https://politifact.com', 0.90),
        ('snopes', 'https://snopes.com', 0.88),
        ('factcheck', 'https://factcheck.org', 0.89)
    ]
    
    try:
        for source in sources:
            cur.execute("""
                INSERT INTO news_source (source_name, source_url, credibility_rating)
                VALUES (%s, %s, %s)
                ON CONFLICT (source_name) DO NOTHING
            """, source)
        
        conn.commit()
        print("News sources inserted successfully")
    except Exception as e:
        print(f"Error inserting news sources: {e}")
        conn.rollback()
    finally:
        cur.close()

def insert_news_categories(conn):
    """Insert news categories"""
    cur = conn.cursor()
    
    categories = [
        ('politics', 'Political news and events'),
        ('entertainment', 'Celebrity and entertainment news'),
        ('health', 'Health and medical news'),
        ('science', 'Science and technology news'),
        ('business', 'Business and finance news'),
        ('sports', 'Sports news and events'),
        ('crime', 'Crime and justice news'),
        ('education', 'Education news'),
        ('environment', 'Environmental news'),
        ('technology', 'Technology news')
    ]
    
    try:
        for category in categories:
            cur.execute("""
                INSERT INTO news_category (category_name, description)
                VALUES (%s, %s)
                ON CONFLICT (category_name) DO NOTHING
            """, category)
        
        conn.commit()
        print("News categories inserted successfully")
    except Exception as e:
        print(f"Error inserting categories: {e}")
        conn.rollback()
    finally:
        cur.close()

def create_sample_users(conn):
    """Create sample users for the system"""
    cur = conn.cursor()
    
    # Sample users with varying follower counts and verification status
    users = []
    
    # Verified users (influencers)
    verified_users = [
        (1001, 'verified_user_1', 'News Analyst Pro', True, random.randint(50000, 100000)),
        (1002, 'verified_user_2', 'Fact Checker Official', True, random.randint(75000, 150000)),
        (1003, 'verified_user_3', 'Media Watch', True, random.randint(100000, 200000)),
        (1004, 'verified_user_4', 'Truth Seeker', True, random.randint(25000, 50000)),
        (1005, 'verified_user_5', 'News Validator', True, random.randint(80000, 120000))
    ]
    
    # Regular users
    for i in range(1, 96):
        user_id = i
        username = f'user_{i}'
        display_name = f'User {i}'
        verified = False
        followers = random.randint(10, 5000)
        users.append((user_id, username, display_name, verified, followers))
    
    users.extend(verified_users)
    
    try:
        for user in users:
            cur.execute("""
                INSERT INTO users (user_id, username, display_name, verified, followers_count, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, user + (datetime.now(),))
        
        conn.commit()
        print(f"Created {len(users)} sample users")
    except Exception as e:
        print(f"Error creating users: {e}")
        conn.rollback()
    finally:
        cur.close()

def import_news_articles(conn):
    """Import news articles from CSV files"""
    cur = conn.cursor()
    
    # Get source IDs
    cur.execute("SELECT source_id, source_name FROM news_source")
    sources = {name.lower(): sid for sid, name in cur.fetchall()}
    
    # Get category IDs
    cur.execute("SELECT category_id, category_name FROM news_category")
    categories = {name: cid for cid, name in cur.fetchall()}
    
    files = [
        ('gossipcop_fake.csv', 'fake', 'gossipcop'),
        ('gossipcop_real.csv', 'real', 'gossipcop'),
        ('politifact_fake.csv', 'fake', 'politifact'),
        ('politifact_real.csv', 'real', 'politifact')
    ]
    
    article_count = 0
    
    for filename, label, source_name in files:
        filepath = os.path.join(DATA_PATH, filename)
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        
        source_id = sources.get(source_name)
        if not source_id:
            print(f"Source not found: {source_name}")
            continue
        
        print(f"Processing {filename}...")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Insert article
                    article_id = f"{source_name}_{article_count + 1}"
                    title = row.get('title', '')[:500]  # Limit title length
                    url = row.get('news_url', row.get('url', ''))[:500]
                    
                    if not title or not url:
                        continue
                    
                    cur.execute("""
                        INSERT INTO news_article (article_id, source_id, title, url, label, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (article_id) DO NOTHING
                    """, (article_id, source_id, title, url, label, datetime.now()))
                    
                    article_count += 1
                    
                    # Insert content if available
                    content = row.get('content', row.get('text', ''))
                    if content:
                        cur.execute("""
                            INSERT INTO news_content (article_id, text)
                            VALUES (%s, %s)
                            ON CONFLICT (article_id) DO NOTHING
                        """, (article_id, content))
                        
                        # Assign random category
                        if source_name == 'gossipcop':
                            category_id = categories.get('entertainment')
                        else:
                            category_id = categories.get('politics')
                        
                        if category_id:
                            cur.execute("""
                                INSERT INTO article_category (article_id, category_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                            """, (article_id, category_id))
                
                except Exception as e:
                    print(f"Error inserting article: {e}")
                    continue
        
        conn.commit()
        print(f"Processed {filename} - Total articles: {article_count}")
    
    cur.close()
    print(f"Total articles imported: {article_count}")

def create_sample_tweets(conn):
    """Create sample tweets and retweets for the articles"""
    cur = conn.cursor()
    
    # Get all articles
    cur.execute("SELECT article_id FROM news_article LIMIT 1000")
    articles = [row[0] for row in cur.fetchall()]
    
    # Get all users
    cur.execute("SELECT user_id FROM users")
    users = [row[0] for row in cur.fetchall()]
    
    if not articles or not users:
        print("No articles or users found")
        return
    
    tweet_count = 0
    retweet_count = 0
    
    try:
        # Create tweets
        for article_id in articles[:500]:  # Limit to first 500 articles
            # Random number of tweets per article (1-10)
            num_tweets = random.randint(1, 10)
            
            for _ in range(num_tweets):
                user_id = random.choice(users)
                tweet_text = f"Check out this article! #news #fakenews"
                retweet_count_val = random.randint(0, 100)
                favorite_count = random.randint(0, 200)
                
                tweet_id = random.randint(100000000, 999999999)
                cur.execute("""
                    INSERT INTO tweet (tweet_id, user_id, article_id, content, retweet_count, 
                                     favorite_count, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tweet_id) DO NOTHING
                """, (tweet_id, user_id, article_id, tweet_text, retweet_count_val, 
                     favorite_count, datetime.now()))
                tweet_count += 1
                
                # Create retweets for popular tweets
                if retweet_count_val > 20:
                    num_retweets = min(retweet_count_val, 20)  # Limit retweets
                    retweeters = random.sample(users, min(num_retweets, len(users)))
                    
                    for retweeter_id in retweeters:
                        if retweeter_id != user_id:  # Don't retweet own tweet
                            cur.execute("""
                                INSERT INTO retweet (tweet_id, user_id, retweeted_at)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (tweet_id, user_id) DO NOTHING
                            """, (tweet_id, retweeter_id, datetime.now()))
                            retweet_count += 1
        
        conn.commit()
        print(f"Created {tweet_count} tweets and {retweet_count} retweets")
        
    except Exception as e:
        print(f"Error creating tweets: {e}")
        conn.rollback()
    finally:
        cur.close()

def main():
    """Main function to run the import process"""
    print("Starting FakeNewsNet data import...")
    
    # Check if data directory exists
    if not os.path.exists(DATA_PATH):
        print(f"Data directory not found: {DATA_PATH}")
        print("Please extract the fakenewsnet.zip file first")
        return
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Create tables
        create_tables_if_not_exists(conn)
        
        # Import data
        insert_news_sources(conn)
        insert_news_categories(conn)
        create_sample_users(conn)
        import_news_articles(conn)
        create_sample_tweets(conn)
        
        print("\nData import completed successfully!")
        
        # Print summary
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM news_article")
        article_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM tweet")
        tweet_count = cur.fetchone()[0]
        
        print(f"\nDatabase Summary:")
        print(f"- Articles: {article_count}")
        print(f"- Users: {user_count}")
        print(f"- Tweets: {tweet_count}")
        
        cur.close()
        
    except Exception as e:
        print(f"Error during import: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()