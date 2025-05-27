# Este arquivo é o ponto de entrada principal da aplicação
from __init__ import create_app, db
from models import User, Student, LessonType, Payment, Notification, File
import socket
import os


app = create_app()

if __name__ == '__main__':
    # Cria as tabelas do banco de dados se não existirem
    with app.app_context():
        # Garante que todos os modelos sejam importados
        print("Criando tabelas do banco de dados...")
        db.create_all()
        print("Tabelas criadas com sucesso!")
    
    # Configurações do servidor
    HOST = '0.0.0.0'  # Permite acesso de qualquer endereço IP
    PORT = 5000
    
    # Obtém o endereço IP da máquina na rede local
    def get_local_ip():
        try:
            # Cria um socket para se conectar a um servidor externo
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            # Não é necessário realmente se conectar
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"Não foi possível obter o endereço IP local: {e}")
            return "127.0.0.1"  # Retorna localhost como fallback
    
    local_ip = get_local_ip()
    
    # Cria o diretório de uploads se não existir
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Configura a pasta de uploads no app
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Inicia o servidor de desenvolvimento
    print("\n" + "="*60)
    print(f"Sistema de Gerenciamento de Alunos")
    print("="*60)
    print(f"Acesso local:       http://127.0.0.1:{PORT}")
    print(f"Acesso na rede:     http://{local_ip}:{PORT}")
    print("="*60)
    print("Pressione CTRL+C para encerrar o servidor")
    print("="*60 + "\n")
    
    # Inicia o servidor Flask
    app.run(host=HOST, port=PORT, debug=True, threaded=True)