-- FakeNewsNet Database Queries
-- Capstone Project 2 - Complete Deliverable Set

-- ============================================
-- EASY QUERIES (2 Required)
-- ============================================

-- Easy Query 1: Total Tweets by News Label
-- This query counts total tweets and calculates average retweets for fake vs real news
SELECT 
    na.label,
    COUNT(t.tweet_id) as total_tweets,
    AVG(t.retweet_count) as avg_retweets
FROM news_article na
INNER JOIN tweet t ON na.article_id = t.article_id
GROUP BY na.label
ORDER BY total_tweets DESC;

-- Easy Query 2: User Activity Summary
-- Identifies most active users with over 1000 followers
SELECT 
    u.username,
    u.verified,
    COUNT(t.tweet_id) as tweet_count,
    SUM(t.retweet_count) as total_retweets_received
FROM users u
INNER JOIN tweet t ON u.user_id = t.user_id
WHERE u.followers_count > 1000
GROUP BY u.user_id, u.username, u.verified
ORDER BY tweet_count DESC
LIMIT 10;

-- ============================================
-- MEDIUM QUERIES (2 Required)
-- ============================================

-- Medium Query 1: News Source Performance Analysis
-- Analyzes news source performance across categories with string manipulation
SELECT 
    ns.source_name,
    nc.category_name,
    na.label,
    COUNT(DISTINCT na.article_id) as article_count,
    COUNT(DISTINCT t.tweet_id) as total_tweets,
    COUNT(DISTINCT t.user_id) as unique_users,
    UPPER(SUBSTRING(na.title, 1, 50)) || '...' as sample_title
FROM news_source ns
INNER JOIN news_article na ON ns.source_id = na.source_id
INNER JOIN article_category ac ON na.article_id = ac.article_id
INNER JOIN news_category nc ON ac.category_id = nc.category_id
LEFT JOIN tweet t ON na.article_id = t.article_id
WHERE na.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY ns.source_name, nc.category_name, na.label, na.title
HAVING COUNT(DISTINCT t.tweet_id) > 0
ORDER BY total_tweets DESC;

-- Medium Query 2: Viral Content Detection
-- Finds viral content with retweet patterns from verified users
SELECT 
    na.title,
    ns.source_name,
    na.label,
    COUNT(DISTINCT t.tweet_id) as original_tweets,
    COUNT(DISTINCT r.retweet_id) as total_retweets,
    COUNT(DISTINCT r.user_id) as unique_retweeters,
    ROUND(COUNT(DISTINCT r.retweet_id)::DECIMAL / 
          NULLIF(COUNT(DISTINCT t.tweet_id), 0), 2) as retweet_ratio,
    LOWER(TRIM(u.username)) as top_influencer
FROM news_article na
INNER JOIN news_source ns ON na.source_id = ns.source_id
INNER JOIN tweet t ON na.article_id = t.article_id
INNER JOIN users u ON t.user_id = u.user_id
LEFT JOIN retweet r ON t.tweet_id = r.tweet_id
WHERE t.created_at >= CURRENT_DATE - INTERVAL '7 days'
  AND u.verified = true
GROUP BY na.article_id, na.title, ns.source_name, na.label, u.username
HAVING COUNT(DISTINCT r.retweet_id) > 0
ORDER BY retweet_ratio DESC
LIMIT 20;

-- ============================================
-- DIFFICULT QUERY (1 Required)
-- ============================================

-- Difficult Query: Comprehensive Fake News Network Analysis
-- Complex analysis using CTEs, nested queries, multiple joins, and various functions
WITH user_influence AS (
    -- Calculate user influence scores
    SELECT 
        u.user_id,
        u.username,
        u.verified,
        u.followers_count,
        COUNT(DISTINCT t.tweet_id) as tweet_count,
        AVG(t.retweet_count) as avg_retweets,
        RANK() OVER (ORDER BY u.followers_count * 
                     COUNT(DISTINCT t.tweet_id) DESC) as influence_rank
    FROM users u
    INNER JOIN tweet t ON u.user_id = t.user_id
    GROUP BY u.user_id, u.username, u.verified, u.followers_count
),
article_metrics AS (
    -- Calculate article engagement metrics
    SELECT 
        na.article_id,
        na.title,
        na.label,
        ns.source_name,
        nc.text,
        COUNT(DISTINCT t.tweet_id) as tweet_count,
        COUNT(DISTINCT t.user_id) as unique_users,
        SUM(t.retweet_count) as total_retweets,
        EXTRACT(DAY FROM MAX(t.created_at) - MIN(t.created_at)) as spread_days
    FROM news_article na
    INNER JOIN news_source ns ON na.source_id = ns.source_id
    LEFT JOIN news_content nc ON na.article_id = nc.article_id
    INNER JOIN tweet t ON na.article_id = t.article_id
    WHERE na.created_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY na.article_id, na.title, na.label, ns.source_name, nc.text
)
SELECT 
    am.source_name,
    am.label,
    UPPER(LEFT(am.title, 60)) || '...' as article_title,
    am.tweet_count,
    am.unique_users,
    am.total_retweets,
    am.spread_days,
    ui.username as top_influencer,
    ui.verified as influencer_verified,
    ui.influence_rank,
    uf.follower_count as influencer_network_size,
    DATE_TRUNC('week', t.created_at) as tweet_week,
    COUNT(DISTINCT 
        CASE WHEN ncat.category_name = 'Politics' 
        THEN t.tweet_id END) as political_tweets,
    ROUND(am.total_retweets::DECIMAL / 
          NULLIF(am.tweet_count, 0), 2) as avg_retweet_rate
FROM article_metrics am
INNER JOIN tweet t ON am.article_id = t.article_id
INNER JOIN user_influence ui ON t.user_id = ui.user_id
INNER JOIN article_category ac ON am.article_id = ac.article_id
INNER JOIN news_category ncat ON ac.category_id = ncat.category_id
LEFT JOIN (
    SELECT following_id, COUNT(*) as follower_count
    FROM user_follower
    GROUP BY following_id
) uf ON ui.user_id = uf.following_id
WHERE am.label = 'fake'
  AND ui.influence_rank <= 100
  AND am.spread_days >= 0
  AND LENGTH(am.title) > 20
GROUP BY am.source_name, am.label, am.title, am.tweet_count, 
         am.unique_users, am.total_retweets, am.spread_days,
         ui.username, ui.verified, ui.influence_rank, 
         uf.follower_count, tweet_week
HAVING COUNT(DISTINCT t.tweet_id) > 0
ORDER BY ui.influence_rank, am.total_retweets DESC
LIMIT 25;

-- ============================================
-- ADDITIONAL DEMONSTRATION QUERIES
-- ============================================

-- Query 6: Most Retweeted Fake News
-- Demonstrates ORDER BY and aggregation
SELECT 
    na.title,
    ns.source_name,
    COUNT(DISTINCT t.tweet_id) as tweet_count,
    SUM(t.retweet_count) as total_retweets
FROM news_article na
INNER JOIN news_source ns ON na.source_id = ns.source_id
INNER JOIN tweet t ON na.article_id = t.article_id
WHERE na.label = 'fake'
GROUP BY na.article_id, na.title, ns.source_name
ORDER BY total_retweets DESC
LIMIT 10;

-- Query 7: User Network Analysis
-- Demonstrates complex joins and calculations
SELECT 
    u1.username as user,
    u1.verified,
    COUNT(DISTINCT uf.follower_id) as follower_count,
    COUNT(DISTINCT uf2.following_id) as following_count,
    ROUND(COUNT(DISTINCT uf.follower_id)::DECIMAL / 
          NULLIF(COUNT(DISTINCT uf2.following_id), 0), 2) as follower_ratio
FROM users u1
LEFT JOIN user_follower uf ON u1.user_id = uf.following_id
LEFT JOIN user_follower uf2 ON u1.user_id = uf2.follower_id
GROUP BY u1.user_id, u1.username, u1.verified
HAVING COUNT(DISTINCT uf.follower_id) > 0
ORDER BY follower_count DESC;

-- Query 8: Timeline Analysis
-- Demonstrates date functions and temporal analysis
SELECT 
    DATE_TRUNC('day', t.created_at) as tweet_date,
    na.label,
    COUNT(*) as tweets_per_day,
    AVG(t.retweet_count) as avg_retweets,
    COUNT(DISTINCT t.user_id) as unique_users
FROM tweet t
INNER JOIN news_article na ON t.article_id = na.article_id
WHERE t.created_at >= CURRENT_DATE - INTERVAL '14 days'
GROUP BY DATE_TRUNC('day', t.created_at), na.label
ORDER BY tweet_date DESC, na.label;