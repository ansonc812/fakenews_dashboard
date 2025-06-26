from flask import Blueprint, request, jsonify
from app.models import NewsArticle, NewsSource, User, Tweet, NewsCategory
from app.database import db
from sqlalchemy import or_, and_, func
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/articles', methods=['GET'])
def get_articles():
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filters
    label = request.args.get('label')  # 'fake' or 'real'
    source_id = request.args.get('source_id', type=int)
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search')
    
    # Build query
    query = NewsArticle.query
    
    if label:
        query = query.filter(NewsArticle.label == label)
    if source_id:
        query = query.filter(NewsArticle.source_id == source_id)
    if category_id:
        query = query.join(NewsArticle.categories).filter(NewsCategory.category_id == category_id)
    if search:
        query = query.filter(NewsArticle.title.ilike(f'%{search}%'))
    
    # Execute with pagination
    articles = query.order_by(NewsArticle.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Format results
    results = []
    for article in articles.items:
        results.append({
            'article_id': article.article_id,
            'title': article.title,
            'url': article.url,
            'label': article.label,
            'source': article.source.source_name if article.source else None,
            'created_at': article.created_at.isoformat() if article.created_at else None,
            'categories': [cat.category_name for cat in article.categories]
        })
    
    return jsonify({
        'articles': results,
        'total': articles.total,
        'pages': articles.pages,
        'current_page': page
    })

@api_bp.route('/sources', methods=['GET'])
def get_sources():
    sources = NewsSource.query.all()
    results = []
    for source in sources:
        results.append({
            'source_id': source.source_id,
            'source_name': source.source_name,
            'source_url': source.source_url,
            'credibility_rating': float(source.credibility_rating) if source.credibility_rating else None
        })
    return jsonify(results)

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = NewsCategory.query.all()
    results = []
    for category in categories:
        results.append({
            'category_id': category.category_id,
            'category_name': category.category_name,
            'description': category.description
        })
    return jsonify(results)

@api_bp.route('/stats/overview', methods=['GET'])
def get_overview_stats():
    # Get overall statistics
    total_articles = NewsArticle.query.count()
    fake_articles = NewsArticle.query.filter_by(label='fake').count()
    real_articles = NewsArticle.query.filter_by(label='real').count()
    
    total_users = User.query.count()
    verified_users = User.query.filter_by(verified=True).count()
    
    total_tweets = Tweet.query.count()
    total_retweets = db.session.query(func.sum(Tweet.retweet_count)).scalar() or 0
    
    return jsonify({
        'articles': {
            'total': total_articles,
            'fake': fake_articles,
            'real': real_articles,
            'fake_percentage': round(fake_articles / total_articles * 100, 2) if total_articles > 0 else 0
        },
        'users': {
            'total': total_users,
            'verified': verified_users,
            'unverified': total_users - verified_users,
            'verified_percentage': round(verified_users / total_users * 100, 2) if total_users > 0 else 0
        },
        'engagement': {
            'total_tweets': total_tweets,
            'total_retweets': total_retweets,
            'avg_retweets_per_tweet': round(total_retweets / total_tweets, 2) if total_tweets > 0 else 0
        }
    })

@api_bp.route('/articles/<int:article_id>', methods=['GET'])
def get_article_detail(article_id):
    article = NewsArticle.query.get_or_404(article_id)
    
    # Get engagement metrics
    tweet_count = article.tweets.count()
    total_retweets = db.session.query(func.sum(Tweet.retweet_count)).filter(
        Tweet.article_id == article_id
    ).scalar() or 0
    total_favorites = db.session.query(func.sum(Tweet.favorite_count)).filter(
        Tweet.article_id == article_id
    ).scalar() or 0
    
    # Get top tweets
    top_tweets = article.tweets.order_by(Tweet.retweet_count.desc()).limit(5).all()
    
    return jsonify({
        'article_id': article.article_id,
        'title': article.title,
        'url': article.url,
        'label': article.label,
        'created_at': article.created_at.isoformat() if article.created_at else None,
        'source': {
            'source_id': article.source.source_id,
            'source_name': article.source.source_name,
            'credibility_rating': float(article.source.credibility_rating) if article.source.credibility_rating else None
        } if article.source else None,
        'content': {
            'text': article.content.text if article.content else None,
            'author': article.content.author if article.content else None,
            'publish_date': article.content.publish_date.isoformat() if article.content and article.content.publish_date else None,
            'word_count': article.content.word_count if article.content else None
        },
        'categories': [{'id': cat.category_id, 'name': cat.category_name} for cat in article.categories],
        'engagement': {
            'tweet_count': tweet_count,
            'total_retweets': total_retweets,
            'total_favorites': total_favorites
        },
        'top_tweets': [{
            'tweet_id': tweet.tweet_id,
            'username': tweet.user.username if tweet.user else None,
            'verified': tweet.user.verified if tweet.user else False,
            'content': tweet.content,
            'retweet_count': tweet.retweet_count,
            'favorite_count': tweet.favorite_count
        } for tweet in top_tweets]
    })

@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    tweet_count = user.tweets.count()
    articles_shared = db.session.query(func.count(func.distinct(Tweet.article_id))).filter(
        Tweet.user_id == user_id
    ).scalar()
    
    # Get fake vs real news sharing
    fake_shared = db.session.query(func.count(Tweet.tweet_id)).join(
        NewsArticle
    ).filter(
        and_(Tweet.user_id == user_id, NewsArticle.label == 'fake')
    ).scalar()
    
    real_shared = db.session.query(func.count(Tweet.tweet_id)).join(
        NewsArticle
    ).filter(
        and_(Tweet.user_id == user_id, NewsArticle.label == 'real')
    ).scalar()
    
    return jsonify({
        'user_id': user.user_id,
        'username': user.username,
        'display_name': user.display_name,
        'verified': user.verified,
        'followers_count': user.followers_count,
        'following_count': user.following_count,
        'tweets_count': user.tweets_count,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'activity': {
            'total_tweets': tweet_count,
            'articles_shared': articles_shared,
            'fake_news_tweets': fake_shared,
            'real_news_tweets': real_shared,
            'fake_news_percentage': round(fake_shared / tweet_count * 100, 2) if tweet_count > 0 else 0
        }
    })