"""
Ponto de entrada WSGI para servidores como Gunicorn
"""
from config import ProductionConfig
from student_system import create_app
from run import setup_logging, create_admin_user

# Criação da aplicação Flask com a configuração de produção
app = create_app(ProductionConfig)

# Configurações auxiliares para produção
setup_logging(app)
create_admin_user(app)
