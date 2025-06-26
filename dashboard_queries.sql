-- Dashboard SQL Queries for Fake News Detection System
-- These queries are used by the Flask application to retrieve data for the dashboards

-- ============================================================================
-- OPERATIONAL DASHBOARD QUERIES
-- ============================================================================

-- 1. Viral Content Detection Query
-- Identifies articles with high engagement velocity in the last N hours
SELECT 
    na.article_id,
    na.title,
    na.url,
    na.label,
    COUNT(t.tweet_id) as tweet_count,
    COALESCE(SUM(t.retweet_count), 0) as total_retweets,
    COALESCE(SUM(t.favorite_count), 0) as total_favorites,
    (COALESCE(SUM(t.retweet_count), 0) * 2 + 
     COALESCE(SUM(t.favorite_count), 0) + 
     COUNT(t.tweet_id) * 0.5) as engagement_score
FROM news_article na
JOIN tweet t ON na.article_id = t.article_id
WHERE t.created_at >= (NOW() - INTERVAL '24 hours')
GROUP BY na.article_id, na.title, na.url, na.label
ORDER BY total_retweets DESC
LIMIT 20;

-- 2. Top Influencers Query
-- Finds users with highest impact spreading news (fake or real)
SELECT 
    u.user_id,
    u.username,
    u.display_name,
    u.verified,
    u.followers_count,
    COUNT(t.tweet_id) as tweet_count,
    COALESCE(SUM(t.retweet_count), 0) as total_impact
FROM users u
JOIN tweet t ON u.user_id = t.user_id
JOIN news_article na ON t.article_id = na.article_id
WHERE na.label = 'fake' -- Can be parameterised to filter by news type
GROUP BY u.user_id, u.username, u.display_name, u.verified, u.followers_count
ORDER BY total_impact DESC
LIMIT 50;

-- 3. Source Credibility Analysis
-- Calculates credibility metrics for each news source
SELECT 
    ns.source_id,
    ns.source_name,
    ns.credibility_rating,
    COUNT(na.article_id) as article_count,
    SUM(CASE WHEN na.label = 'fake' THEN 1 ELSE 0 END) as fake_count,
    SUM(CASE WHEN na.label = 'real' THEN 1 ELSE 0 END) as real_count,
    ROUND(
        SUM(CASE WHEN na.label = 'fake' THEN 1 ELSE 0 END) * 100.0 / 
        COUNT(na.article_id), 2
    ) as fake_percentage
FROM news_source ns
JOIN news_article na ON ns.source_id = na.source_id
GROUP BY ns.source_id, ns.source_name, ns.credibility_rating
ORDER BY fake_percentage DESC;

-- 4. Category Distribution (Real-time)
-- Shows distribution of fake vs real news by category in the last N hours
SELECT 
    nc.category_name,
    COUNT(na.article_id) as total_articles,
    SUM(CASE WHEN na.label = 'fake' THEN 1 ELSE 0 END) as fake_articles,
    SUM(CASE WHEN na.label = 'real' THEN 1 ELSE 0 END) as real_articles,
    ROUND(
        SUM(CASE WHEN na.label = 'fake' THEN 1 ELSE 0 END) * 100.0 / 
        COUNT(na.article_id), 2
    ) as fake_percentage
FROM news_category nc
JOIN article_category ac ON nc.category_id = ac.category_id
JOIN news_article na ON ac.article_id = na.article_id
WHERE na.created_at >= (NOW() - INTERVAL '24 hours')
GROUP BY nc.category_id, nc.category_name
ORDER BY total_articles DESC;

-- ============================================================================
-- ANALYTICAL DASHBOARD QUERIES
-- ============================================================================

-- 5. Temporal Trends Analysis
-- Daily trends of fake vs real news over the last N days
SELECT 
    DATE(na.created_at) as date,
    na.label,
    COUNT(na.article_id) as count
FROM news_article na
WHERE na.created_at >= (NOW() - INTERVAL '30 days')
GROUP BY DATE(na.created_at), na.label
ORDER BY date;

-- 6. Network Analysis - Key Spreaders
-- Identifies key nodes in the information spreading network
SELECT 
    u.user_id,
    u.username,
    u.verified,
    COUNT(DISTINCT t.article_id) as articles_shared,
    SUM(t.retweet_count) as total_reach,
    CASE 
        WHEN u.verified THEN 'verified'
        WHEN SUM(t.retweet_count) > 10000 THEN 'high_impact'
        ELSE 'regular'
    END as node_type
FROM users u
JOIN tweet t ON u.user_id = t.user_id
GROUP BY u.user_id, u.username, u.verified
ORDER BY total_reach DESC
LIMIT 100;

-- 7. Network Analysis - Connections (Retweet Relationships)
-- Maps connections between users through retweet relationships
SELECT 
    rt.user_id as retweeter,
    t.user_id as original_poster,
    COUNT(rt.retweet_id) as connection_strength
FROM retweet rt
JOIN tweet t ON rt.tweet_id = t.tweet_id
WHERE rt.user_id IN (SELECT user_id FROM users ORDER BY followers_count DESC LIMIT 100)
  AND t.user_id IN (SELECT user_id FROM users ORDER BY followers_count DESC LIMIT 100)
GROUP BY rt.user_id, t.user_id
HAVING COUNT(rt.retweet_id) >= 3
ORDER BY connection_strength DESC;

-- 8. Category Performance Over Time
-- Monthly performance metrics by category
SELECT 
    DATE_TRUNC('month', na.created_at) as month,
    nc.category_name,
    na.label,
    COUNT(na.article_id) as count,
    AVG(t.retweet_count) as avg_retweets
FROM news_article na
JOIN article_category ac ON na.article_id = ac.article_id
JOIN news_category nc ON ac.category_id = nc.category_id
JOIN tweet t ON na.article_id = t.article_id
WHERE na.created_at >= (NOW() - INTERVAL '6 months')
GROUP BY DATE_TRUNC('month', na.created_at), nc.category_name, na.label
ORDER BY month, nc.category_name;

-- 9. User Behavior Analysis
-- Analyzes behavior patterns of verified vs unverified users
SELECT 
    u.verified,
    na.label,
    COUNT(DISTINCT u.user_id) as user_count,
    COUNT(t.tweet_id) as tweet_count,
    AVG(u.followers_count) as avg_followers,
    SUM(t.retweet_count) as total_reach,
    ROUND(COUNT(t.tweet_id) * 1.0 / COUNT(DISTINCT u.user_id), 2) as tweets_per_user
FROM users u
JOIN tweet t ON u.user_id = t.user_id
JOIN news_article na ON t.article_id = na.article_id
GROUP BY u.verified, na.label
ORDER BY u.verified, na.label;

-- 10. Source Reliability Timeline
-- Tracks source reliability over time
SELECT 
    DATE_TRUNC('month', na.created_at) as month,
    ns.source_name,
    COUNT(na.article_id) as total_articles,
    SUM(CASE WHEN na.label = 'fake' THEN 1 ELSE 0 END) as fake_count,
    ROUND(
        SUM(CASE WHEN na.label = 'real' THEN 1 ELSE 0 END) * 100.0 / 
        COUNT(na.article_id), 2
    ) as reliability_score
FROM news_article na
JOIN news_source ns ON na.source_id = ns.source_id
WHERE na.created_at >= (NOW() - INTERVAL '12 months')
GROUP BY DATE_TRUNC('month', na.created_at), ns.source_id, ns.source_name
HAVING COUNT(na.article_id) >= 10
ORDER BY month, ns.source_name;

-- ============================================================================
-- PERFORMANCE OPTIMIZATION QUERIES
-- ============================================================================

-- Indexes for optimal performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tweet_created_at ON tweet(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tweet_article_id ON tweet(article_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tweet_user_id ON tweet(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_created_at ON news_article(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_label ON news_article(label);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_retweet_user_tweet ON retweet(user_id, tweet_id);

-- ============================================================================
-- MATERIALIZED VIEWS FOR DASHBOARD PERFORMANCE
-- ============================================================================

-- Materialized view for daily statistics (refreshed hourly)
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_news_stats AS
SELECT 
    DATE(created_at) as news_date,
    label,
    COUNT(*) as article_count,
    COUNT(DISTINCT source_id) as unique_sources
FROM news_article
WHERE created_at >= (NOW() - INTERVAL '90 days')
GROUP BY DATE(created_at), label;

-- Index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_stats_date_label 
ON daily_news_stats(news_date, label);

-- Refresh command (to be run periodically)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY daily_news_stats;

-- ============================================================================
-- AGGREGATION FUNCTIONS FOR DASHBOARD METRICS
-- ============================================================================

-- Function to calculate engagement score
CREATE OR REPLACE FUNCTION calculate_engagement_score(
    retweets INTEGER,
    favorites INTEGER,
    tweets INTEGER
) RETURNS DECIMAL AS $$
BEGIN
    RETURN (COALESCE(retweets, 0) * 2 + 
            COALESCE(favorites, 0) + 
            COALESCE(tweets, 0) * 0.5);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to get viral threshold (articles above 95th percentile of engagement)
CREATE OR REPLACE FUNCTION get_viral_threshold(hours_back INTEGER DEFAULT 24)
RETURNS DECIMAL AS $$
DECLARE
    threshold DECIMAL;
BEGIN
    SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY engagement_score)
    INTO threshold
    FROM (
        SELECT calculate_engagement_score(
            SUM(t.retweet_count),
            SUM(t.favorite_count),
            COUNT(t.tweet_id)
        ) as engagement_score
        FROM news_article na
        JOIN tweet t ON na.article_id = t.article_id
        WHERE t.created_at >= (NOW() - INTERVAL hours_back || ' hours')
        GROUP BY na.article_id
    ) scores;
    
    RETURN COALESCE(threshold, 0);
END;
$$ LANGUAGE plpgsql;