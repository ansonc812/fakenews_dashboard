from flask import Blueprint, render_template, request, jsonify
from app.models import NewsArticle, NewsSource, User, Tweet, NewsCategory, ArticleCategory
from app.database import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta

operational_bp = Blueprint('operational', __name__)

@operational_bp.route('/')
def index():
    return render_template('operational/dashboard.html')

@operational_bp.route('/operational')
def operational_dashboard():
    return render_template('operational/dashboard.html')

@operational_bp.route('/operational/viral-content')
def viral_content():
    # Get time range from query params (default: last 24 hours)
    hours = request.args.get('hours', 24, type=int)
    label_filter = request.args.get('label', None)  # 'fake', 'real', or None for all
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # Query for viral content
    query = db.session.query(
        NewsArticle,
        func.count(Tweet.tweet_id).label('tweet_count'),
        func.sum(Tweet.retweet_count).label('total_retweets'),
        func.sum(Tweet.favorite_count).label('total_favorites')
    ).join(
        Tweet, NewsArticle.article_id == Tweet.article_id
    ).filter(
        Tweet.created_at >= time_threshold
    )
    
    # Add label filter if specified
    if label_filter:
        query = query.filter(NewsArticle.label == label_filter)
    
    viral_articles = query.group_by(
        NewsArticle.article_id
    ).order_by(
        desc('total_retweets')
    ).limit(20).all()
    
    results = []
    for article, tweet_count, retweets, favorites in viral_articles:
        results.append({
            'article_id': article.article_id,
            'title': article.title,
            'url': article.url,
            'label': article.label,
            'tweet_count': tweet_count,
            'retweet_count': retweets or 0,
            'favorite_count': favorites or 0,
            'engagement_score': (retweets or 0) * 2 + (favorites or 0) + tweet_count * 0.5
        })
    
    return jsonify(results)

@operational_bp.route('/operational/influencers')
def top_influencers():
    # Get influencers spreading news
    label_filter = request.args.get('label', None)  # 'fake', 'real', or None for all
    
    query = db.session.query(
        User,
        func.count(Tweet.tweet_id).label('tweet_count'),
        func.sum(Tweet.retweet_count).label('total_impact')
    ).join(
        Tweet, User.user_id == Tweet.user_id
    ).join(
        NewsArticle, Tweet.article_id == NewsArticle.article_id
    )
    
    if label_filter:
        query = query.filter(NewsArticle.label == label_filter)
    
    influencers = query.group_by(
        User.user_id
    ).order_by(
        desc('total_impact')
    ).limit(50).all()
    
    results = []
    for user, tweet_count, impact in influencers:
        results.append({
            'user_id': user.user_id,
            'username': user.username,
            'display_name': user.display_name,
            'verified': user.verified,
            'followers_count': user.followers_count,
            'tweet_count': tweet_count,
            'impact_score': impact or 0
        })
    
    return jsonify(results)

@operational_bp.route('/operational/source-credibility')
def source_credibility():
    # Real-time source credibility metrics
    sources = db.session.query(
        NewsSource,
        func.count(NewsArticle.article_id).label('article_count'),
        func.sum(func.cast(NewsArticle.label == 'fake', db.Integer)).label('fake_count'),
        func.sum(func.cast(NewsArticle.label == 'real', db.Integer)).label('real_count')
    ).join(
        NewsArticle, NewsSource.source_id == NewsArticle.source_id
    ).group_by(
        NewsSource.source_id
    ).all()
    
    results = []
    for source, total, fake, real in sources:
        fake_ratio = (fake / total * 100) if total > 0 else 0
        results.append({
            'source_id': source.source_id,
            'source_name': source.source_name,
            'credibility_rating': float(source.credibility_rating) if source.credibility_rating else None,
            'article_count': total,
            'fake_count': fake or 0,
            'real_count': real or 0,
            'fake_percentage': round(fake_ratio, 2)
        })
    
    return jsonify(results)

@operational_bp.route('/operational/category-distribution')
def category_distribution():
    # Current distribution by category
    hours = request.args.get('hours', 24, type=int)
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    distribution = db.session.query(
        NewsCategory.category_name,
        func.count(NewsArticle.article_id).label('total'),
        func.sum(func.cast(NewsArticle.label == 'fake', db.Integer)).label('fake_count')
    ).join(
        ArticleCategory, NewsCategory.category_id == ArticleCategory.category_id
    ).join(
        NewsArticle, ArticleCategory.article_id == NewsArticle.article_id
    ).filter(
        NewsArticle.created_at >= time_threshold
    ).group_by(
        NewsCategory.category_id, NewsCategory.category_name
    ).all()
    
    results = []
    for category, total, fake in distribution:
        results.append({
            'category': category,
            'total_articles': total,
            'fake_articles': fake or 0,
            'real_articles': total - (fake or 0),
            'fake_percentage': round((fake or 0) / total * 100, 2) if total > 0 else 0
        })
    
    return jsonify(results)