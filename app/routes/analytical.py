from flask import Blueprint, render_template, request, jsonify
from app.models import NewsArticle, NewsSource, User, Tweet, NewsCategory, Retweet, ArticleCategory
from app.database import db
from sqlalchemy import func, desc, and_, or_, distinct
from datetime import datetime, timedelta
import json

analytical_bp = Blueprint('analytical', __name__)

@analytical_bp.route('/analytical')
def analytical_dashboard():
    return render_template('analytical/dashboard.html')

@analytical_bp.route('/analytical/temporal-trends')
def temporal_trends():
    # Get date range from query params
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query for daily trends
    daily_trends = db.session.query(
        func.date(NewsArticle.created_at).label('date'),
        NewsArticle.label,
        func.count(NewsArticle.article_id).label('count')
    ).filter(
        NewsArticle.created_at.between(start_date, end_date)
    ).group_by(
        func.date(NewsArticle.created_at),
        NewsArticle.label
    ).order_by(
        func.date(NewsArticle.created_at)
    ).all()
    
    # Format results for time series
    results = {}
    for date, label, count in daily_trends:
        date_str = date.isoformat()
        if date_str not in results:
            results[date_str] = {'date': date_str, 'fake': 0, 'real': 0}
        results[date_str][label] = count
    
    return jsonify(list(results.values()))

@analytical_bp.route('/analytical/network-analysis')
def network_analysis():
    # Get top spreaders and their networks
    limit = request.args.get('limit', 100, type=int)
    
    # Find key nodes in the network
    key_spreaders = db.session.query(
        User.user_id,
        User.username,
        User.verified,
        func.count(distinct(Tweet.article_id)).label('articles_shared'),
        func.sum(Tweet.retweet_count).label('total_reach')
    ).join(
        Tweet, User.user_id == Tweet.user_id
    ).group_by(
        User.user_id
    ).order_by(
        desc('total_reach')
    ).limit(limit).all()
    
    # Get connections between users (retweet relationships)
    user_ids = [u[0] for u in key_spreaders]
    
    connections = db.session.query(
        Retweet.user_id.label('retweeter'),
        Tweet.user_id.label('original_poster'),
        func.count(Retweet.retweet_id).label('connection_strength')
    ).join(
        Tweet, Retweet.tweet_id == Tweet.tweet_id
    ).filter(
        and_(
            Retweet.user_id.in_(user_ids),
            Tweet.user_id.in_(user_ids)
        )
    ).group_by(
        Retweet.user_id,
        Tweet.user_id
    ).all()
    
    # Format for network visualization
    nodes = []
    for user_id, username, verified, articles, reach in key_spreaders:
        nodes.append({
            'id': user_id,
            'label': username,
            'verified': verified,
            'articles_shared': articles,
            'reach': reach or 0,
            'size': min(50, max(10, (reach or 0) / 1000))  # Node size based on reach
        })
    
    edges = []
    for retweeter, poster, strength in connections:
        if retweeter != poster:  # Exclude self-connections
            edges.append({
                'source': poster,
                'target': retweeter,
                'weight': strength
            })
    
    return jsonify({'nodes': nodes, 'edges': edges})

@analytical_bp.route('/analytical/category-performance')
def category_performance():
    # Analyze performance across categories over time
    months = request.args.get('months', 6, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=months * 30)
    
    # Get monthly category performance
    performance = db.session.query(
        func.date_trunc('month', NewsArticle.created_at).label('month'),
        NewsCategory.category_name,
        NewsArticle.label,
        func.count(NewsArticle.article_id).label('count'),
        func.avg(Tweet.retweet_count).label('avg_retweets')
    ).join(
        ArticleCategory, NewsArticle.article_id == ArticleCategory.article_id
    ).join(
        NewsCategory, ArticleCategory.category_id == NewsCategory.category_id
    ).join(
        Tweet, NewsArticle.article_id == Tweet.article_id
    ).filter(
        NewsArticle.created_at >= start_date
    ).group_by(
        func.date_trunc('month', NewsArticle.created_at),
        NewsCategory.category_name,
        NewsArticle.label
    ).all()
    
    # Format as heatmap data
    results = {}
    for month, category, label, count, avg_retweets in performance:
        month_str = month.strftime('%Y-%m')
        key = f"{category}_{label}"
        if key not in results:
            results[key] = {
                'category': category,
                'label': label,
                'data': {}
            }
        results[key]['data'][month_str] = {
            'count': count,
            'avg_engagement': float(avg_retweets) if avg_retweets else 0
        }
    
    return jsonify(list(results.values()))

@analytical_bp.route('/analytical/user-behavior')
def user_behavior_analysis():
    # Analyze user behavior patterns
    
    # Verified vs Unverified user spreading patterns
    user_patterns = db.session.query(
        User.verified,
        NewsArticle.label,
        func.count(distinct(User.user_id)).label('user_count'),
        func.count(Tweet.tweet_id).label('tweet_count'),
        func.avg(User.followers_count).label('avg_followers'),
        func.sum(Tweet.retweet_count).label('total_reach')
    ).join(
        Tweet, User.user_id == Tweet.user_id
    ).join(
        NewsArticle, Tweet.article_id == NewsArticle.article_id
    ).group_by(
        User.verified,
        NewsArticle.label
    ).all()
    
    results = []
    for verified, label, users, tweets, avg_followers, reach in user_patterns:
        results.append({
            'user_type': 'Verified' if verified else 'Unverified',
            'news_type': label,
            'unique_users': users,
            'total_tweets': tweets,
            'avg_followers': float(avg_followers) if avg_followers else 0,
            'total_reach': reach or 0,
            'tweets_per_user': tweets / users if users > 0 else 0
        })
    
    return jsonify(results)

@analytical_bp.route('/analytical/source-timeline')
def source_reliability_timeline():
    # Track source reliability over time
    months = request.args.get('months', 12, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=months * 30)
    
    # Get monthly source performance
    timeline = db.session.query(
        func.date_trunc('month', NewsArticle.created_at).label('month'),
        NewsSource.source_name,
        func.count(NewsArticle.article_id).label('total'),
        func.sum(func.cast(NewsArticle.label == 'fake', db.Integer)).label('fake_count'),
        func.sum(func.cast(NewsArticle.label == 'real', db.Integer)).label('real_count')
    ).join(
        NewsSource, NewsArticle.source_id == NewsSource.source_id
    ).filter(
        NewsArticle.created_at >= start_date
    ).group_by(
        func.date_trunc('month', NewsArticle.created_at),
        NewsSource.source_id,
        NewsSource.source_name
    ).having(
        func.count(NewsArticle.article_id) >= 5  # Only sources with sufficient data
    ).all()
    
    # Format timeline data
    results = {}
    for month, source, total, fake, real in timeline:
        month_str = month.strftime('%Y-%m')
        reliability_score = (real / total * 100) if total > 0 else 0
        if source not in results:
            results[source] = {
                'source_name': source,
                'timeline': []
            }
        results[source]['timeline'].append({
            'month': month_str,
            'total_articles': total,
            'fake_articles': fake or 0,
            'reliability_score': reliability_score
        })
    
    return jsonify(list(results.values()))