# main.py
from app import app, db
from models import User
import logging

# Configurar o logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    with app.app_context():
        # Criar tabelas do banco de dados
        db.create_all()
        
        # Criar usuário administrador se não existir
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin')
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Usuário administrador criado com sucesso!")
    
    # Iniciar o servidor
    app.run(host="0.0.0.0", port=5000, debug=True)
    