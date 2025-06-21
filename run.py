#!/usr/bin/env python3
"""
Ponto de entrada principal para o Sistema de Gerenciamento de Alunos
"""
import os
import socket
import secrets
import string
from student_system import create_app, db
from student_system.models import User
from werkzeug.security import generate_password_hash
import logging
from logging.handlers import RotatingFileHandler

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_local_ip():
    """Obtém o endereço IP da máquina na rede local"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.warning(f"Não foi possível obter o endereço IP local: {e}")
        return "127.0.0.1"

def generate_secure_password(length=12):
    """Gera uma senha segura aleatória"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

def create_admin_user(app):
    """Cria o usuário administrador padrão se não existir"""
    with app.app_context():
        # Garantir que o diretório instance existe
        instance_path = app.instance_path
        os.makedirs(instance_path, exist_ok=True)
        
        # Criar tabelas do banco de dados
        try:
            db.create_all()
            logger.info("Tabelas do banco de dados criadas com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            raise
        
        # Criar usuário administrador se não existir
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Gerar senha segura apenas em desenvolvimento
            if app.config.get('DEBUG', False):
                admin_password = 'admin'
                logger.warning("⚠️  SENHA PADRÃO 'admin' USADA - ALTERE IMEDIATAMENTE EM PRODUÇÃO!")
            else:
                admin_password = generate_secure_password()
                logger.info(f"Senha do administrador gerada: {admin_password}")
                logger.warning("⚠️  SALVE ESTA SENHA EM LOCAL SEGURO!")
            
            admin = User(
                username='admin',
                password_hash=generate_password_hash(admin_password)
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Usuário administrador criado com sucesso!")
        else:
            logger.info("Usuário administrador já existe.")

def setup_logging(app):
    """Configura logging para produção"""
    if not app.debug and not app.testing:
        # Criar diretório de logs se não existir
        if not os.path.exists('logs'):
            os.makedirs('logs', exist_ok=True)
        
        # Configurar log de arquivo
        file_handler = RotatingFileHandler('logs/student_system.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sistema de Gerenciamento de Alunos iniciado')

def main():
    """Função principal para iniciar a aplicação"""
    # Determinar ambiente
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Criar a aplicação Flask com configuração apropriada
    if env == 'production':
        from config import ProductionConfig
        app = create_app(ProductionConfig)
    elif env == 'testing':
        from config import TestingConfig
        app = create_app(TestingConfig)
    else:
        from config import DevelopmentConfig
        app = create_app(DevelopmentConfig)
    
    # Configurar logging
    setup_logging(app)
    
    # Criar usuário admin e tabelas
    create_admin_user(app)
    
    # Configurações do servidor
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Verificar se é produção
    if env == 'production':
        print("\n" + "="*60)
        print("🚀 MODO PRODUÇÃO ATIVADO")
        print("="*60)
        print("⚠️  IMPORTANTE:")
        print("   - Certifique-se de que SECRET_KEY está configurada")
        print("   - Use um servidor WSGI como Gunicorn")
        print("   - Configure HTTPS")
        print("   - Monitore os logs em logs/student_system.log")
        print("="*60)
        
        # Em produção, não usar o servidor de desenvolvimento do Flask
        print("❌ NÃO USE ESTE COMANDO EM PRODUÇÃO!")
        print("Use: gunicorn -w 4 -b 0.0.0.0:5000 run:app")
        print("="*60)
        return
    else:
        # Obter IP local
        local_ip = get_local_ip()
        
        # Exibir informações de acesso
        print("\n" + "="*60)
        print(f"Sistema de Gerenciamento de Alunos - {env.upper()}")
        print("="*60)
        print(f"Acesso local:       http://127.0.0.1:{PORT}")
        print(f"Acesso na rede:     http://{local_ip}:{PORT}")
        print("="*60)
        print("Credenciais padrão:")
        print("  Usuário: admin")
        print("  Senha:   admin")
        print("="*60)
        print("⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!")
        print("="*60)
        print("Pressione CTRL+C para encerrar o servidor")
        print("="*60 + "\n")
        
        # Iniciar o servidor Flask (apenas desenvolvimento)
        app.run(host=HOST, port=PORT, debug=app.config.get('DEBUG', False), threaded=True)

if __name__ == '__main__':
    main() 