# __init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
import os
from datetime import datetime
import sqlite3

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configuração de upload de arquivos
    app.config['ALLOWED_EXTENSIONS'] = {
        'jpg', 'jpeg', 'png', 'gif',  # Imagens
        'pdf',  # Documentos PDF
        'doc', 'docx',  # Documentos do Word
        'xls', 'xlsx',  # Planilhas do Excel
        'mp3', 'wav',  # Áudio
        'mp4', 'avi'  # Vídeos
    }
    
    # Configuração do diretório de uploads (usando a raiz do projeto para facilitar o acesso)
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    print(f"Diretório de uploads configurado em: {upload_folder}")
    
    # Configurações para URLs externas
    app.config['PREFERRED_URL_SCHEME'] = 'http'  # Usar 'https' em produção com SSL
    app.config['SERVER_NAME'] = None  # Será configurado dinamicamente no app.py
    
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Database configuration
    db_path = os.path.join(app.instance_path, 'music_school.db')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        'pool_pre_ping': True,
        "pool_recycle": 300,
    }
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User  # Importação absoluta
        return User.query.get(int(user_id))
    
    # Register blueprints
    from auth import auth_bp  # Importação absoluta
    from routes import main_bp  # Importação absoluta
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    # Context processor
    @app.context_processor
    def inject_globals():
        return {'now': datetime.now()}
    
    return app