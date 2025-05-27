#!/usr/bin/env python
# migrate_db.py
from app import app, db
from flask_migrate import Migrate, upgrade, migrate as migrate_cmd, init, stamp

# Inicializa o Flask-Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    import sys
    from flask_migrate.cli import db as db_cli
    
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        with app.app_context():
            print("Inicializando o diretório de migrações...")
            init()
            print("Diretório de migrações inicializado com sucesso!")
    
    elif len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        with app.app_context():
            print("Criando migração...")
            migrate_cmd(message=' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'migração automática')
            print("Migração criada com sucesso!")
    
    elif len(sys.argv) > 1 and sys.argv[1] == 'upgrade':
        with app.app_context():
            print("Aplicando migrações pendentes...")
            upgrade()
            print("Migrações aplicadas com sucesso!")
    
    else:
        print("Uso: python migrate_db.py <comando>")
        print("Comandos disponíveis:")
        print("  init      - Inicializa o diretório de migrações")
        print("  migrate   - Cria uma nova migração")
        print("  upgrade   - Aplica as migrações pendentes")
