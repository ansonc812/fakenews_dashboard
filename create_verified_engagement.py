#!/usr/bin/env python3
"""
Create Verified User Engagement Data
This script creates tweets and engagement from verified users to fix the user behavior patterns
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

def create_verified_user_tweets(conn):
    """Create tweets from verified users for better analytics"""
    cur = conn.cursor()
    
    try:
        # Get verified users
        cur.execute("SELECT user_id, username FROM users WHERE verified = true")
        verified_users = cur.fetchall()
        
        if not verified_users:
            print("No verified users found")
            return
        
        # Get sample articles (mix of fake and real)
        cur.execute("""
            SELECT article_id, label FROM news_article 
            ORDER BY RANDOM() 
            LIMIT 200
        """)
        articles = cur.fetchall()
        
        tweet_count = 0
        retweet_count = 0
        
        # Create tweets from verified users
        for user_id, username in verified_users:
            # Each verified user tweets about 10-30 articles
            num_tweets = random.randint(10, 30)
            user_articles = random.sample(articles, min(num_tweets, len(articles)))
            
            for article_id, label in user_articles:
                # Create tweet
                tweet_id = random.randint(2000000000, 9999999999)
                
                # Verified users tweet differently about fake vs real news
                if label == 'fake':
                    # Verified users are more likely to fact-check or warn about fake news
                    tweet_texts = [
                        f"⚠️ This article needs fact-checking. Be cautious about sharing. #FactCheck",
                        f"🧐 Questionable claims in this article. Always verify sources! #MediaLiteracy",
                        f"❌ This doesn't align with verified information. #FactCheck #News",
                        f"🔍 Investigating this claim - preliminary findings suggest it's misleading.",
                        f"📰 PSA: This article contains unverified information. Please fact-check!"
                    ]
                    retweet_count_base = random.randint(20, 100)  # Lower engagement for fact-checking
                    favorite_count_base = random.randint(50, 200)
                else:
                    # Verified users promote real news more enthusiastically  
                    tweet_texts = [
                        f"✅ Important and verified news everyone should read. #News #TrustWorthySource",
                        f"📢 Sharing this well-researched article. Great journalism! #News",
                        f"👍 Solid reporting on an important issue. Worth reading. #QualityNews", 
                        f"📰 Excellent piece with proper sourcing and fact-checking. #Journalism",
                        f"🎯 This article presents the facts clearly and objectively. #News"
                    ]
                    retweet_count_base = random.randint(50, 300)  # Higher engagement for real news
                    favorite_count_base = random.randint(100, 500)
                
                tweet_text = random.choice(tweet_texts)
                
                # Create the tweet
                cur.execute("""
                    INSERT INTO tweet (tweet_id, user_id, article_id, content, retweet_count, 
                                     favorite_count, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tweet_id) DO NOTHING
                """, (tweet_id, user_id, article_id, tweet_text, retweet_count_base, 
                     favorite_count_base, datetime.now() - timedelta(days=random.randint(1, 90))))
                
                tweet_count += 1
                
                # Create retweets from other users (verified users get more engagement)
                if retweet_count_base > 30:
                    # Get random users to create retweets
                    cur.execute("SELECT user_id FROM users WHERE user_id != %s ORDER BY RANDOM() LIMIT %s", 
                              (user_id, min(retweet_count_base // 5, 20)))
                    retweeters = [row[0] for row in cur.fetchall()]
                    
                    for retweeter_id in retweeters:
                        cur.execute("""
                            INSERT INTO retweet (tweet_id, user_id, retweeted_at)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (tweet_id, user_id) DO NOTHING
                        """, (tweet_id, retweeter_id, datetime.now() - timedelta(days=random.randint(1, 60))))
                        retweet_count += 1
        
        conn.commit()
        print(f"Created {tweet_count} verified user tweets and {retweet_count} additional retweets")
        
    except Exception as e:
        print(f"Error creating verified user tweets: {e}")
        conn.rollback()
    finally:
        cur.close()

def update_user_follower_counts(conn):
    """Update follower counts for verified users to be more realistic"""
    cur = conn.cursor()
    
    try:
        # Update verified users to have higher follower counts
        cur.execute("""
            UPDATE users 
            SET followers_count = 
                CASE 
                    WHEN verified = true THEN followers_count + %s
                    ELSE followers_count
                END
        """, (random.randint(20000, 100000),))
        
        conn.commit()
        print("Updated verified user follower counts")
        
    except Exception as e:
        print(f"Error updating follower counts: {e}")
        conn.rollback()
    finally:
        cur.close()

def main():
    """Main function to create verified user engagement"""
    print("Creating verified user engagement data...")
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        create_verified_user_tweets(conn)
        update_user_follower_counts(conn)
        
        print("\nVerified user engagement data created successfully!")
        
        # Print summary
        cur = conn.cursor()
        
        # Count tweets by user type
        cur.execute("""
            SELECT u.verified, COUNT(t.tweet_id) 
            FROM users u 
            JOIN tweet t ON u.user_id = t.user_id 
            GROUP BY u.verified
        """)
        
        print(f"\nTweet Summary by User Type:")
        for verified, count in cur.fetchall():
            user_type = "Verified" if verified else "Unverified"
            print(f"- {user_type}: {count} tweets")
        
        # Count total users
        cur.execute("SELECT verified, COUNT(*) FROM users GROUP BY verified")
        print(f"\nUser Summary:")
        for verified, count in cur.fetchall():
            user_type = "Verified" if verified else "Unverified"
            print(f"- {user_type}: {count} users")
        
        cur.close()
        
    except Exception as e:
        print(f"Error during creation: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()