#!/usr/bin/env python3
"""
Script de deploy para produção
"""
import os
import sys
import subprocess
import secrets
import string
from pathlib import Path

def generate_secret_key(length=32):
    """Gera uma chave secreta segura"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

def check_requirements():
    """Verifica se todos os requisitos estão atendidos"""
    print("🔍 Verificando requisitos...")
    
    # Verificar se Python 3.10+ está instalado
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 ou superior é necessário")
        return False
    
    # Verificar se pip está instalado
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ pip não está instalado")
        return False
    
    print("✅ Requisitos atendidos")
    return True

def setup_environment():
    """Configura o ambiente de produção"""
    print("🔧 Configurando ambiente...")
    
    # Criar arquivo .env se não existir
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Criando arquivo .env...")
        secret_key = generate_secret_key()
        
        env_content = f"""# Configurações de Produção
FLASK_ENV=production
SECRET_KEY={secret_key}
DATABASE_URL=sqlite:///instance/app.db
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=WARNING
BACKUP_ENABLED=true
BACKUP_PATH=backups
MAX_CONTENT_LENGTH=16777216
PERMANENT_SESSION_LIFETIME=28800
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Arquivo .env criado com SECRET_KEY: {secret_key}")
        print("⚠️  SALVE ESTA CHAVE EM LOCAL SEGURO!")
    else:
        print("✅ Arquivo .env já existe")
    
    # Criar diretórios necessários
    directories = ['logs', 'backups', 'uploads', 'instance']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Diretório {directory} criado/verificado")

def install_dependencies():
    """Instala as dependências"""
    print("📦 Instalando dependências...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependências instaladas")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def setup_database():
    """Configura o banco de dados"""
    print("🗄️ Configurando banco de dados...")
    
    try:
        # Executar migrações
        subprocess.run([sys.executable, "migrate_db.py", "upgrade"], check=True)
        print("✅ Banco de dados configurado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao configurar banco de dados: {e}")
        return False

def create_gunicorn_config():
    """Cria arquivo de configuração do Gunicorn"""
    print("🐳 Criando configuração do Gunicorn...")
    
    gunicorn_config = """# Gunicorn configuration file
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
reload = False
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True
"""
    
    with open("gunicorn.conf.py", "w") as f:
        f.write(gunicorn_config)
    
    print("✅ Configuração do Gunicorn criada")

def create_systemd_service():
    """Cria arquivo de serviço systemd"""
    print("🔧 Criando serviço systemd...")
    
    current_dir = os.getcwd()
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=Sistema de Gerenciamento de Alunos
After=network.target

[Service]
Type=exec
User={os.getenv('USER', 'www-data')}
WorkingDirectory={current_dir}
Environment=PATH={os.path.dirname(python_path)}:$PATH
Environment=FLASK_ENV=production
ExecStart={python_path} -m gunicorn -c gunicorn.conf.py run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open("student-management.service", "w") as f:
        f.write(service_content)
    
    print("✅ Arquivo de serviço systemd criado")
    print("📋 Para instalar o serviço:")
    print("   sudo cp student-management.service /etc/systemd/system/")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable student-management")
    print("   sudo systemctl start student-management")

def main():
    """Função principal"""
    print("🚀 Script de Deploy para Produção")
    print("=" * 50)
    
    # Verificar requisitos
    if not check_requirements():
        sys.exit(1)
    
    # Configurar ambiente
    setup_environment()
    
    # Instalar dependências
    if not install_dependencies():
        sys.exit(1)
    
    # Configurar banco de dados
    if not setup_database():
        sys.exit(1)
    
    # Criar configuração do Gunicorn
    create_gunicorn_config()
    
    # Criar serviço systemd
    create_systemd_service()
    
    print("\n" + "=" * 50)
    print("✅ Deploy concluído com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Configure o arquivo .env com suas configurações")
    print("2. Teste a aplicação: python run.py")
    print("3. Para produção, use: gunicorn -c gunicorn.conf.py run:app")
    print("4. Configure HTTPS com Nginx/Apache")
    print("5. Configure backup automático")
    print("6. Monitore os logs em logs/")
    print("\n⚠️  IMPORTANTE:")
    print("- Altere a senha do administrador após o primeiro login")
    print("- Configure firewall adequadamente")
    print("- Faça backup regular do banco de dados")
    print("- Monitore o uso de recursos")

if __name__ == "__main__":
    main() 