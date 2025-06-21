import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, faça o login para acessar esta página."

def create_app(config_class=None):
    # Cria a aplicação Flask com configuração de instância
    app = Flask(__name__, instance_relative_config=True)

    # Carrega a configuração
    if config_class:
        app.config.from_object(config_class)
    else:
        # Fallback para configuração padrão
        app.config.from_object('config.Config')

    # Inicializa configurações específicas do ambiente
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    # Cria a pasta de instância se não existir
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Cria a pasta de uploads se não existir
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Configuração de upload de arquivos
    app.config['ALLOWED_EXTENSIONS'] = {
        'jpg', 'jpeg', 'png', 'gif',  # Imagens
        'pdf',  # Documentos PDF
        'doc', 'docx',  # Documentos do Word
        'xls', 'xlsx',  # Planilhas do Excel
        'mp3', 'wav',  # Áudio
        'mp4', 'avi'  # Vídeos
    }

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # Configurar sessão permanente
    app.config['PERMANENT_SESSION_LIFETIME'] = app.config.get('PERMANENT_SESSION_LIFETIME', 28800)  # 8 horas

    with app.app_context():
        # Importa as rotas e blueprints
        from . import routes, auth, models

        # Registra o blueprint de autenticação
        app.register_blueprint(auth.bp)
        
        # Registra o blueprint das rotas principais
        app.register_blueprint(routes.bp)
        
        # Context processor para variáveis globais
        @app.context_processor
        def inject_globals():
            return {'now': datetime.now()}

        # Error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            from flask import render_template
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            from flask import render_template
            db.session.rollback()
            return render_template('errors/500.html'), 500

    return app 