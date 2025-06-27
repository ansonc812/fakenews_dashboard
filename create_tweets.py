#!/usr/bin/env python3
"""
Script to create sample tweets for existing articles
"""

import psycopg2
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fakenewsnet')

def create_tweets_for_articles():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Get all articles
    cur.execute("SELECT article_id FROM news_article LIMIT 2000")  # Limit for performance
    articles = [row[0] for row in cur.fetchall()]
    
    # Get all users
    cur.execute("SELECT user_id FROM users")
    users = [row[0] for row in cur.fetchall()]
    
    if not users:
        print("No users found! Need to run import_data.py first")
        return
    
    print(f"Creating tweets for {len(articles)} articles with {len(users)} users...")
    
    tweet_count = 0
    retweet_count = 0
    
    for i, article_id in enumerate(articles):
        if i % 500 == 0:
            print(f"Processing article {i+1}/{len(articles)}")
        
        # Random number of tweets per article (0-8, with most having 1-3)
        num_tweets = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8], 
                                   weights=[20, 30, 25, 15, 5, 2, 1, 1, 1])[0]
        
        if num_tweets == 0:
            continue
            
        # Create random creation time within last 30 days
        base_time = datetime.now() - timedelta(days=random.randint(0, 30))
        
        for j in range(num_tweets):
            user_id = random.choice(users)
            tweet_id = random.randint(100000000000, 999999999999)  # 12-digit tweet ID
            
            # Tweet content variety
            tweet_texts = [
                "This is important news! #breaking #news",
                "Everyone should read this article #mustread",
                "Interesting story here #news #trending",
                "This changes everything! #important",
                "Can't believe this happened #shocking",
                "Great reporting on this story #journalism",
                "This is so relevant right now #current",
                "Amazing story, thanks for sharing #awesome",
                "This is concerning... #worried #news",
                "Excellent piece of journalism #quality"
            ]
            
            tweet_text = random.choice(tweet_texts)
            
            # Engagement metrics - make some tweets more viral
            if random.random() < 0.1:  # 10% chance of viral tweet
                retweet_count_val = random.randint(50, 500)
                favorite_count = random.randint(100, 1000)
            elif random.random() < 0.3:  # 30% chance of popular tweet
                retweet_count_val = random.randint(10, 100)
                favorite_count = random.randint(20, 200)
            else:  # Regular tweet
                retweet_count_val = random.randint(0, 20)
                favorite_count = random.randint(0, 50)
            
            # Tweet creation time
            tweet_time = base_time + timedelta(minutes=j*10)
            
            try:
                cur.execute("""
                    INSERT INTO tweet (tweet_id, user_id, article_id, content, retweet_count, 
                                     favorite_count, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tweet_id) DO NOTHING
                """, (tweet_id, user_id, article_id, tweet_text, retweet_count_val, 
                     favorite_count, tweet_time))
                
                tweet_count += 1
                
                # Create retweets for popular tweets
                if retweet_count_val > 5:
                    num_retweets = min(retweet_count_val // 3, 20)  # Limit retweets
                    retweeter_ids = random.sample(users, min(num_retweets, len(users)))
                    
                    for k, retweeter_id in enumerate(retweeter_ids):
                        if retweeter_id != user_id:  # Don't retweet own tweet
                            retweet_time = tweet_time + timedelta(minutes=k*5 + random.randint(1, 60))
                            try:
                                cur.execute("""
                                    INSERT INTO retweet (tweet_id, user_id, retweeted_at)
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT (tweet_id, user_id) DO NOTHING
                                """, (tweet_id, retweeter_id, retweet_time))
                                retweet_count += 1
                            except:
                                pass  # Ignore retweet conflicts
                
            except Exception as e:
                print(f"Error creating tweet for article {article_id}: {e}")
                continue
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\nCreated {tweet_count} tweets and {retweet_count} retweets!")

if __name__ == "__main__":
    create_tweets_for_articles()