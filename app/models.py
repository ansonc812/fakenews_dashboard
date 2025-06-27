from app.database import db
from datetime import datetime

class NewsSource(db.Model):
    __tablename__ = 'news_source'
    
    source_id = db.Column(db.Integer, primary_key=True)
    source_name = db.Column(db.String(100), nullable=False)
    source_url = db.Column(db.String(255))
    credibility_rating = db.Column(db.Numeric(3, 2))
    
    # Relationships
    articles = db.relationship('NewsArticle', back_populates='source', lazy='dynamic')

class NewsArticle(db.Model):
    __tablename__ = 'news_article'
    
    article_id = db.Column(db.String(50), primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('news_source.source_id'))
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    label = db.Column(db.String(10), nullable=False)  # 'fake' or 'real'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    source = db.relationship('NewsSource', back_populates='articles')
    content = db.relationship('NewsContent', back_populates='article', uselist=False)
    images = db.relationship('NewsImage', back_populates='article', lazy='dynamic')
    tweets = db.relationship('Tweet', back_populates='article', lazy='dynamic')
    categories = db.relationship('NewsCategory', secondary='article_category', 
                                back_populates='articles', lazy='dynamic')

class NewsContent(db.Model):
    __tablename__ = 'news_content'
    
    content_id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.String(50), db.ForeignKey('news_article.article_id'), unique=True)
    text = db.Column(db.Text)
    publish_date = db.Column(db.DateTime)
    author = db.Column(db.String(255))
    word_count = db.Column(db.Integer)
    
    # Relationships
    article = db.relationship('NewsArticle', back_populates='content')

class NewsImage(db.Model):
    __tablename__ = 'news_image'
    
    image_id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.String(50), db.ForeignKey('news_article.article_id'))
    image_url = db.Column(db.String(500))
    caption = db.Column(db.String(500))
    position = db.Column(db.Integer)
    
    # Relationships
    article = db.relationship('NewsArticle', back_populates='images')

class NewsCategory(db.Model):
    __tablename__ = 'news_category'
    
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Relationships
    articles = db.relationship('NewsArticle', secondary='article_category', 
                              back_populates='categories', lazy='dynamic')

class ArticleCategory(db.Model):
    __tablename__ = 'article_category'
    
    article_id = db.Column(db.String(50), db.ForeignKey('news_article.article_id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('news_category.category_id'), primary_key=True)

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(50))
    display_name = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False)
    followers_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime)
    
    # Relationships
    tweets = db.relationship('Tweet', back_populates='user', lazy='dynamic')
    retweets = db.relationship('Retweet', back_populates='user', lazy='dynamic')
    timeline = db.relationship('UserTimeline', back_populates='user', lazy='dynamic')

class Tweet(db.Model):
    __tablename__ = 'tweet'
    
    tweet_id = db.Column(db.BigInteger, primary_key=True)
    article_id = db.Column(db.String(50), db.ForeignKey('news_article.article_id'))
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'))
    content = db.Column(db.String(280))
    created_at = db.Column(db.DateTime)
    retweet_count = db.Column(db.Integer, default=0)
    favorite_count = db.Column(db.Integer, default=0)
    
    # Relationships
    article = db.relationship('NewsArticle', back_populates='tweets')
    user = db.relationship('User', back_populates='tweets')
    retweets = db.relationship('Retweet', back_populates='tweet', lazy='dynamic')

class Retweet(db.Model):
    __tablename__ = 'retweet'
    
    retweet_id = db.Column(db.BigInteger, primary_key=True)
    tweet_id = db.Column(db.BigInteger, db.ForeignKey('tweet.tweet_id'))
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'))
    retweeted_at = db.Column(db.DateTime)
    
    # Relationships
    tweet = db.relationship('Tweet', back_populates='retweets')
    user = db.relationship('User', back_populates='retweets')

class UserFollower(db.Model):
    __tablename__ = 'user_follower'
    
    follower_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), primary_key=True)
    following_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), primary_key=True)
    followed_at = db.Column(db.DateTime)

class UserTimeline(db.Model):
    __tablename__ = 'user_timeline'
    
    timeline_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'))
    tweet_content = db.Column(db.String(280))
    tweet_date = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', back_populates='timeline')