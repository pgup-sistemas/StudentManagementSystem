import os
from datetime import timedelta

class Config:
    # Configuração de segurança - OBRIGATÓRIO para produção
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuração do banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuração de uploads
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    
    # Configurações de segurança adicionais
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuração de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Configuração de upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Configuração de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Configuração de backup
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'false').lower() == 'true'
    BACKUP_PATH = os.environ.get('BACKUP_PATH', 'backups')

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    
    # Em desenvolvimento, usar chave secreta padrão se não definida
    @classmethod
    def init_app(cls, app):
        if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            import secrets
            import string
            characters = string.ascii_letters + string.digits + string.punctuation
            app.config['SECRET_KEY'] = ''.join(secrets.choice(characters) for _ in range(32))

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Configurações específicas de produção
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Configuração de logging mais rigorosa
    LOG_LEVEL = 'WARNING'
    
    @classmethod
    def init_app(cls, app):
        # Verificar se SECRET_KEY está configurada em produção
        if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY deve ser definida como variável de ambiente em produção")

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' 