import os
import logging
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Define base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")  # Use environment variable in production
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Set 'now' variable for all templates
@app.context_processor
def inject_globals():
    return {
        'now': datetime.now()
    }

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///music_school.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'

# Import models after db initialization to avoid circular imports
with app.app_context():
    from models import User, Student, LessonType, Payment
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create database tables
    db.create_all()
    logging.info("Database tables created")
    
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin')  # Default password, should be changed
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Admin user created")
