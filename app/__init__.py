from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import toml

# Initialize Flask extensions
db = SQLAlchemy()
bootstrap = Bootstrap()

def create_app():
    app = Flask(__name__)
    
    # Load configuration from TOML file
    config = toml.load('config.toml')
    
    # Configure Flask app
    app.config['SECRET_KEY'] = config['app']['secret_key']
    app.config['SQLALCHEMY_DATABASE_URI'] = config['app']['database_url']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    
    # Initialize extensions
    db.init_app(app)
    bootstrap.init_app(app)
    
    # Make bootstrap available to templates
    app.jinja_env.globals['bootstrap'] = bootstrap
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
