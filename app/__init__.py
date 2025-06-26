from flask import Flask
from flask_cors import CORS
from config import Config
from app.database import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.routes.operational import operational_bp
    from app.routes.analytical import analytical_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(operational_bp)
    app.register_blueprint(analytical_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app