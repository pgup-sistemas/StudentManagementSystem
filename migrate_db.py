#!/usr/bin/env python3
"""
Script para gerenciar migrações do banco de dados
"""
from student_system import create_app, db
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python migrate_db.py <comando>")
        print("Comandos disponíveis:")
        print("  init     - Inicializar migrações")
        print("  migrate  - Criar nova migração")
        print("  upgrade  - Aplicar migrações pendentes")
        print("  downgrade - Reverter última migração")
        sys.exit(1)
    
    command = sys.argv[1]
    
    with app.app_context():
        if command == 'init':
            from flask_migrate import init
            init()
            print("Migrações inicializadas com sucesso!")
            
        elif command == 'migrate':
            from flask_migrate import migrate
            message = sys.argv[2] if len(sys.argv) > 2 else "migração automática"
            migrate(message=message)
            print(f"Migração criada: {message}")
            
        elif command == 'upgrade':
            from flask_migrate import upgrade
            upgrade()
            print("Migrações aplicadas com sucesso!")
            
        elif command == 'downgrade':
            from flask_migrate import downgrade
            downgrade()
            print("Última migração revertida!")
            
        else:
            print(f"Comando desconhecido: {command}")
            sys.exit(1)
