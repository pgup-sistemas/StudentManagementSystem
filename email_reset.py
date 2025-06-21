#!/usr/bin/env python3
"""
Exemplo de implementação de redefinição de senha via email
Para usar em produção, adicione as dependências necessárias ao requirements.txt
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from student_system import create_app, db
from student_system.models import User
from config import DevelopmentConfig

class EmailResetService:
    def __init__(self):
        self.app = create_app(DevelopmentConfig)
        
        # Configurações de email (substitua pelos seus dados)
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', 'seu-email@gmail.com')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', 'sua-senha-app')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@seudominio.com')
        
    def send_reset_email(self, user_email, reset_code, reset_url):
        """Envia email de redefinição de senha"""
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Redefinição de Senha - Sistema de Gerenciamento de Alunos'
            msg['From'] = self.from_email
            msg['To'] = user_email
            
            # Corpo do email em HTML
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f8f9fa; }}
                    .code {{ background: #e9ecef; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; margin: 20px 0; }}
                    .button {{ display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
                    .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔐 Redefinição de Senha</h1>
                    </div>
                    <div class="content">
                        <p>Olá!</p>
                        <p>Você solicitou a redefinição de senha do seu usuário no Sistema de Gerenciamento de Alunos.</p>
                        
                        <p><strong>Código de redefinição:</strong></p>
                        <div class="code">{reset_code}</div>
                        
                        <p>Ou clique no link abaixo para redefinir sua senha:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Redefinir Senha</a>
                        </p>
                        
                        <p><strong>Importante:</strong></p>
                        <ul>
                            <li>Este código expira em 15 minutos</li>
                            <li>Se você não solicitou esta redefinição, ignore este email</li>
                            <li>Nunca compartilhe este código com outras pessoas</li>
                        </ul>
                    </div>
                    <div class="footer">
                        <p>Este é um email automático, não responda a esta mensagem.</p>
                        <p>Sistema de Gerenciamento de Alunos</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Corpo do email em texto simples
            text_content = f"""
            Redefinição de Senha - Sistema de Gerenciamento de Alunos
            
            Olá!
            
            Você solicitou a redefinição de senha do seu usuário.
            
            Código de redefinição: {reset_code}
            
            Ou acesse: {reset_url}
            
            Este código expira em 15 minutos.
            Se você não solicitou esta redefinição, ignore este email.
            
            Sistema de Gerenciamento de Alunos
            """
            
            # Anexar conteúdo
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
            return False
    
    def test_email_config(self):
        """Testa a configuração de email"""
        print("🧪 Testando configuração de email...")
        print(f"SMTP Server: {self.smtp_server}:{self.smtp_port}")
        print(f"Username: {self.smtp_username}")
        print(f"From Email: {self.from_email}")
        
        # Testar conexão
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                print("✅ Conexão SMTP bem-sucedida!")
                return True
        except Exception as e:
            print(f"❌ Erro na conexão SMTP: {e}")
            return False

def setup_email_config():
    """Configura as variáveis de ambiente para email"""
    print("📧 Configuração de Email")
    print("=" * 40)
    
    # Criar arquivo .env se não existir
    env_content = """# Configurações de Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
FROM_EMAIL=noreply@seudominio.com
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Arquivo .env criado com configurações de email")
    print("\n📋 Para usar Gmail:")
    print("1. Ative a verificação em duas etapas")
    print("2. Gere uma senha de app")
    print("3. Use a senha de app no SMTP_PASSWORD")
    print("\n⚠️  IMPORTANTE: Configure as variáveis no arquivo .env")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Serviço de redefinição de senha via email")
    parser.add_argument("--setup", action="store_true", help="Configurar variáveis de email")
    parser.add_argument("--test", action="store_true", help="Testar configuração de email")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_email_config()
    elif args.test:
        service = EmailResetService()
        service.test_email_config()
    else:
        print("Uso:")
        print("  python email_reset.py --setup  # Configurar email")
        print("  python email_reset.py --test   # Testar configuração")

if __name__ == "__main__":
    main() 