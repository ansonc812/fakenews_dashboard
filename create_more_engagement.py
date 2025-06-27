#!/usr/bin/env python3
"""
Create more engagement data for recent articles to show in real-time metrics
"""

import psycopg2
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fakenewsnet')

def create_high_engagement_content():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Get recent articles (last 100)
    cur.execute("SELECT article_id FROM news_article ORDER BY created_at DESC LIMIT 100")
    recent_articles = [row[0] for row in cur.fetchall()]
    
    # Get all users
    cur.execute("SELECT user_id FROM users")
    users = [row[0] for row in cur.fetchall()]
    
    print(f"Creating high engagement for {len(recent_articles)} recent articles...")
    
    tweet_count = 0
    
    for article_id in recent_articles:
        # Create 5-15 tweets per article for better engagement
        num_tweets = random.randint(5, 15)
        
        for i in range(num_tweets):
            user_id = random.choice(users)
            tweet_id = random.randint(100000000000, 999999999999)
            
            tweet_texts = [
                "This is breaking news! 🚨 #breaking #news #important",
                "Everyone needs to see this! Share now! #viral #news",
                "This story is everywhere! Can't believe it #trending",
                "MUST READ: This changes everything! #mustread #important",
                "This is going viral for good reason! #viral #share",
                "Breaking: Major development in this story! #breaking",
                "This is the story everyone's talking about! #trending",
                "Incredible reporting! Everyone should read this #journalism",
                "This is huge news! Sharing immediately! #bignews",
                "This story is spreading like wildfire! #viral"
            ]
            
            tweet_text = random.choice(tweet_texts)
            
            # Create much higher engagement for these recent tweets
            if random.random() < 0.4:  # 40% chance of viral tweet
                retweet_count_val = random.randint(100, 1000)
                favorite_count = random.randint(200, 2000)
            elif random.random() < 0.7:  # 70% chance of popular tweet
                retweet_count_val = random.randint(25, 200)
                favorite_count = random.randint(50, 400)
            else:  # Regular tweet but still decent engagement
                retweet_count_val = random.randint(5, 50)
                favorite_count = random.randint(10, 100)
            
            # Recent tweet times (last 24 hours)
            hours_ago = random.randint(0, 24)
            tweet_time = datetime.now() - timedelta(hours=hours_ago, minutes=random.randint(0, 59))
            
            try:
                cur.execute("""
                    INSERT INTO tweet (tweet_id, user_id, article_id, content, retweet_count, 
                                     favorite_count, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tweet_id) DO NOTHING
                """, (tweet_id, user_id, article_id, tweet_text, retweet_count_val, 
                     favorite_count, tweet_time))
                
                tweet_count += 1
                
                # Create more retweets for viral content
                if retweet_count_val > 50:
                    num_retweets = min(retweet_count_val // 5, 30)
                    retweeter_ids = random.sample(users, min(num_retweets, len(users)))
                    
                    for j, retweeter_id in enumerate(retweeter_ids):
                        if retweeter_id != user_id:
                            retweet_time = tweet_time + timedelta(minutes=j*2 + random.randint(1, 30))
                            try:
                                cur.execute("""
                                    INSERT INTO retweet (tweet_id, user_id, retweeted_at)
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT (tweet_id, user_id) DO NOTHING
                                """, (tweet_id, retweeter_id, retweet_time))
                            except:
                                pass
                
            except Exception as e:
                print(f"Error creating tweet: {e}")
                continue
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Created {tweet_count} high-engagement tweets for recent articles!")

if __name__ == "__main__":
    create_high_engagement_content()