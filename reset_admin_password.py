#!/usr/bin/env python3
"""
Script para redefinir a senha do administrador via linha de comando
"""
import os
import sys
import getpass
import secrets
import string
from student_system import create_app, db
from student_system.models import User
from werkzeug.security import generate_password_hash
from config import DevelopmentConfig

def generate_secure_password(length=12):
    """Gera uma senha segura aleatória"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

def reset_admin_password():
    """Redefine a senha do administrador"""
    print("🔐 Redefinição de Senha do Administrador")
    print("=" * 50)
    
    # Criar aplicação
    app = create_app(DevelopmentConfig)
    
    with app.app_context():
        # Verificar se o usuário admin existe
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            print("❌ Usuário administrador não encontrado!")
            print("Execute primeiro: python run.py")
            return False
        
        print(f"✅ Usuário administrador encontrado: {admin.username}")
        
        # Opções de redefinição
        print("\nEscolha uma opção:")
        print("1. Gerar senha aleatória segura")
        print("2. Definir senha manualmente")
        print("3. Cancelar")
        
        choice = input("\nOpção (1-3): ").strip()
        
        if choice == "1":
            # Gerar senha aleatória
            new_password = generate_secure_password()
            print(f"\n🔑 Nova senha gerada: {new_password}")
            print("⚠️  SALVE ESTA SENHA EM LOCAL SEGURO!")
            
        elif choice == "2":
            # Definir senha manualmente
            while True:
                new_password = getpass.getpass("Digite a nova senha: ")
                confirm_password = getpass.getpass("Confirme a nova senha: ")
                
                if new_password != confirm_password:
                    print("❌ As senhas não coincidem!")
                    continue
                
                if len(new_password) < 6:
                    print("❌ A senha deve ter pelo menos 6 caracteres!")
                    continue
                
                break
                
        elif choice == "3":
            print("❌ Operação cancelada.")
            return False
            
        else:
            print("❌ Opção inválida!")
            return False
        
        # Confirmar redefinição
        print(f"\n⚠️  ATENÇÃO: Você está prestes a redefinir a senha do administrador!")
        confirm = input("Digite 'CONFIRMAR' para continuar: ").strip()
        
        if confirm != "CONFIRMAR":
            print("❌ Operação cancelada.")
            return False
        
        # Atualizar senha
        try:
            admin.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            print("\n✅ Senha do administrador redefinida com sucesso!")
            print(f"🔑 Nova senha: {new_password}")
            print("\n📋 Próximos passos:")
            print("1. Acesse o sistema com a nova senha")
            print("2. Altere a senha através da interface web")
            print("3. Mantenha a senha em local seguro")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao redefinir senha: {e}")
            return False

def main():
    """Função principal"""
    try:
        success = reset_admin_password()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 