#!/usr/bin/env python3
"""
LIAR Dataset Import Script
This script imports the LIAR dataset into the PostgreSQL database
"""

import os
import csv
import psycopg2
from datetime import datetime
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fakenewsnet')

# Path to the LIAR dataset
LIAR_PATH = "/home/ansonc812/Documents/git/repos/fakenews_dashboard/project 1+2 deliverables/liar_dataset"

def get_db_connection():
    """Create a database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def map_liar_label(label):
    """Map LIAR labels to our binary fake/real system"""
    # LIAR uses: true, mostly-true, half-true, barely-true, false, pants-fire
    if label in ['true', 'mostly-true']:
        return 'real'
    else:
        return 'fake'

def import_liar_dataset(conn):
    """Import LIAR dataset from TSV files"""
    cur = conn.cursor()
    
    # Get or create LIAR source
    cur.execute("""
        INSERT INTO news_source (source_name, source_url, credibility_rating)
        VALUES ('liar', 'https://www.politifact.com', 0.85)
        ON CONFLICT (source_name) DO UPDATE SET
        source_url = EXCLUDED.source_url,
        credibility_rating = EXCLUDED.credibility_rating
        RETURNING source_id
    """)
    source_id = cur.fetchone()[0]
    
    # Get politics category ID
    cur.execute("SELECT category_id FROM news_category WHERE category_name = 'politics'")
    politics_category_id = cur.fetchone()[0]
    
    files = ['train.tsv', 'test.tsv', 'valid.tsv']
    total_imported = 0
    
    for filename in files:
        filepath = os.path.join(LIAR_PATH, filename)
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        
        print(f"Processing {filename}...")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f, delimiter='\t')
            
            for i, row in enumerate(reader):
                try:
                    # LIAR TSV format: ID, label, statement, subject(s), speaker, job-title, state-info, party-affiliation, barely-true-counts, false-counts, half-true-counts, mostly-true-counts, pants-on-fire-counts, context
                    if len(row) < 3:
                        continue
                    
                    liar_id = row[0]
                    original_label = row[1]
                    statement = row[2]
                    subject = row[3] if len(row) > 3 else 'politics'
                    speaker = row[4] if len(row) > 4 else 'Unknown'
                    
                    # Skip if statement is too short
                    if len(statement) < 10:
                        continue
                    
                    # Map to our binary system
                    label = map_liar_label(original_label)
                    
                    # Create article ID
                    article_id = f"liar_{liar_id}"
                    
                    # Create a synthetic URL
                    url = f"https://www.politifact.com/factchecks/liar_{liar_id}/"
                    
                    # Use statement as title (truncated)
                    title = statement[:500] if len(statement) > 500 else statement
                    
                    # Insert article
                    cur.execute("""
                        INSERT INTO news_article (article_id, source_id, title, url, label, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (article_id) DO NOTHING
                    """, (article_id, source_id, title, url, label, datetime.now()))
                    
                    # Insert content
                    content_text = f"Statement: {statement}"
                    if len(row) > 4:
                        content_text += f"\nSpeaker: {speaker}"
                    if len(row) > 5:
                        content_text += f"\nJob Title: {row[5]}"
                    if len(row) > 7:
                        content_text += f"\nParty: {row[7]}"
                    
                    cur.execute("""
                        INSERT INTO news_content (article_id, text, author)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (article_id) DO NOTHING
                    """, (article_id, content_text, speaker))
                    
                    # Link to politics category
                    cur.execute("""
                        INSERT INTO article_category (article_id, category_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (article_id, politics_category_id))
                    
                    total_imported += 1
                    
                    # Create some sample tweets for this article
                    if random.random() < 0.3:  # 30% chance of having tweets
                        create_sample_tweets_for_article(cur, article_id)
                
                except Exception as e:
                    print(f"Error processing row {i} in {filename}: {e}")
                    continue
        
        conn.commit()
        print(f"Completed {filename}")
    
    cur.close()
    print(f"Total LIAR articles imported: {total_imported}")

def create_sample_tweets_for_article(cur, article_id):
    """Create sample tweets for a LIAR article"""
    # Get random users
    cur.execute("SELECT user_id FROM users ORDER BY RANDOM() LIMIT 5")
    users = [row[0] for row in cur.fetchall()]
    
    if not users:
        return
    
    # Create 1-3 tweets per article
    num_tweets = random.randint(1, 3)
    
    for _ in range(num_tweets):
        user_id = random.choice(users)
        tweet_id = random.randint(1000000000, 9999999999)
        
        # Create tweet content
        tweet_texts = [
            "This fact-check is important! #factcheck #politics",
            "Everyone should read this #news #politics #factcheck",
            "Fact-checking matters in today's world #truth",
            "Important political statement analysis #politics",
            "This needs more attention #factcheck #news"
        ]
        
        tweet_text = random.choice(tweet_texts)
        retweet_count = random.randint(0, 50)
        favorite_count = random.randint(0, 100)
        
        try:
            cur.execute("""
                INSERT INTO tweet (tweet_id, user_id, article_id, content, retweet_count, 
                                 favorite_count, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tweet_id) DO NOTHING
            """, (tweet_id, user_id, article_id, tweet_text, retweet_count, 
                 favorite_count, datetime.now()))
            
            # Create some retweets for popular tweets
            if retweet_count > 10:
                num_retweets = min(retweet_count // 5, 10)  # Limit retweets
                cur.execute("SELECT user_id FROM users ORDER BY RANDOM() LIMIT %s", (num_retweets,))
                retweeters = [row[0] for row in cur.fetchall()]
                
                for retweeter_id in retweeters:
                    if retweeter_id != user_id:  # Don't retweet own tweet
                        cur.execute("""
                            INSERT INTO retweet (tweet_id, user_id, retweeted_at)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (tweet_id, user_id) DO NOTHING
                        """, (tweet_id, retweeter_id, datetime.now()))
        
        except Exception as e:
            print(f"Error creating tweet for article {article_id}: {e}")

def main():
    """Main function to run the LIAR import process"""
    print("Starting LIAR dataset import...")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        import_liar_dataset(conn)
        
        print("\nLIAR data import completed successfully!")
        
        # Print summary
        cur = conn.cursor()
        
        # Count articles by source
        cur.execute("""
            SELECT ns.source_name, COUNT(na.article_id) 
            FROM news_article na 
            JOIN news_source ns ON na.source_id = ns.source_id 
            GROUP BY ns.source_name
        """)
        
        print(f"\nDatabase Summary by Source:")
        for source, count in cur.fetchall():
            print(f"- {source}: {count} articles")
        
        # Count by label
        cur.execute("SELECT label, COUNT(*) FROM news_article GROUP BY label")
        print(f"\nArticles by Label:")
        for label, count in cur.fetchall():
            print(f"- {label}: {count}")
        
        cur.close()
        
    except Exception as e:
        print(f"Error during import: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()