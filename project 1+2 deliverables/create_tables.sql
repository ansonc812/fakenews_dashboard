-- FakeNewsNet Database Creation Script
-- Capstone Project 2
-- Database: PostgreSQL 17

-- Note: Create database manually first: CREATE DATABASE fakenewsnet_db;
-- Then connect to it before running this script

-- Set PostgreSQL 17 specific settings for better performance
SET default_table_access_method = heap;
SET search_path = public;

-- Create ENUM type for news labels
CREATE TYPE news_label AS ENUM ('fake', 'real');

-- Table 1: NewsSource
CREATE TABLE news_source (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL UNIQUE,
    source_url VARCHAR(255),
    credibility_rating DECIMAL(3,2) CHECK (credibility_rating >= 0 AND credibility_rating <= 1)
);

-- Table 2: NewsCategory
CREATE TABLE news_category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255)
);

-- Table 3: NewsArticle
CREATE TABLE news_article (
    article_id VARCHAR(50) PRIMARY KEY,
    source_id INTEGER NOT NULL,
    url VARCHAR(500) NOT NULL,
    title VARCHAR(500) NOT NULL,
    label news_label NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES news_source(source_id)
);

-- Create indexes for NewsArticle
CREATE INDEX idx_news_article_source ON news_article(source_id);
CREATE INDEX idx_news_article_label ON news_article(label);

-- Table 4: NewsContent
CREATE TABLE news_content (
    content_id SERIAL PRIMARY KEY,
    article_id VARCHAR(50) UNIQUE NOT NULL,
    text TEXT,
    publish_date TIMESTAMP,
    author VARCHAR(255),
    word_count INTEGER,
    FOREIGN KEY (article_id) REFERENCES news_article(article_id) ON DELETE CASCADE
);

-- Table 5: NewsImage
CREATE TABLE news_image (
    image_id SERIAL PRIMARY KEY,
    article_id VARCHAR(50) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    caption VARCHAR(500),
    position INTEGER,
    FOREIGN KEY (article_id) REFERENCES news_article(article_id) ON DELETE CASCADE
);

CREATE INDEX idx_news_image_article ON news_image(article_id);

-- Table 6: Users (avoiding reserved word 'user')
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    display_name VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);

-- Table 7: Tweet
CREATE TABLE tweet (
    tweet_id BIGINT PRIMARY KEY,
    article_id VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    content VARCHAR(280),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retweet_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    FOREIGN KEY (article_id) REFERENCES news_article(article_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_tweet_article ON tweet(article_id);
CREATE INDEX idx_tweet_user ON tweet(user_id);
CREATE INDEX idx_tweet_created ON tweet(created_at);

-- Table 8: Retweet
CREATE TABLE retweet (
    retweet_id BIGSERIAL PRIMARY KEY,
    tweet_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    retweeted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tweet_id) REFERENCES tweet(tweet_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(tweet_id, user_id)
);

CREATE INDEX idx_retweet_tweet ON retweet(tweet_id);
CREATE INDEX idx_retweet_user ON retweet(user_id);

-- Table 9: UserFollower
CREATE TABLE user_follower (
    follower_id BIGINT NOT NULL,
    following_id BIGINT NOT NULL,
    followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, following_id),
    FOREIGN KEY (follower_id) REFERENCES users(user_id),
    FOREIGN KEY (following_id) REFERENCES users(user_id),
    CHECK (follower_id != following_id)
);

CREATE INDEX idx_user_follower_following ON user_follower(following_id);

-- Table 10: UserTimeline
CREATE TABLE user_timeline (
    timeline_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    tweet_content VARCHAR(280),
    tweet_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_user_timeline_user ON user_timeline(user_id);
CREATE INDEX idx_user_timeline_date ON user_timeline(tweet_date);

-- Table 11: ArticleCategory (Junction table)
CREATE TABLE article_category (
    article_id VARCHAR(50) NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (article_id, category_id),
    FOREIGN KEY (article_id) REFERENCES news_article(article_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES news_category(category_id)
);

-- PostgreSQL 17 specific optimizations
-- Enable parallel queries for better performance
-- Performance tuning (run manually if needed):
-- ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
-- ALTER SYSTEM SET max_parallel_workers = 8;
-- SELECT pg_reload_conf();

-- Create additional performance indexes
CREATE INDEX idx_tweet_created_user ON tweet(created_at, user_id);
CREATE INDEX idx_news_article_label_source ON news_article(label, source_id);

-- Add comments for documentation
-- COMMENT ON DATABASE fakenewsnet_db IS 'FakeNewsNet database for Capstone Project 2';
COMMENT ON TABLE news_article IS 'Main news articles with fact-checking labels';
COMMENT ON TABLE tweet IS 'Social media posts sharing news articles';
COMMENT ON TABLE users IS 'Twitter users in the system';

-- Grant permissions for application user
-- CREATE USER fakenews_app WITH PASSWORD 'secure_password';
-- GRANT CONNECT ON DATABASE fakenewsnet_db TO fakenews_app;
-- GRANT USAGE ON SCHEMA public TO fakenews_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fakenews_app;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO fakenews_app;