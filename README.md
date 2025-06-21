# Sistema de Gerenciamento de Alunos

Um sistema web completo para gerenciamento de alunos, mensalidades e notificações, desenvolvido com Flask.

## 🏗️ Estrutura do Projeto

O projeto segue o padrão **Application Factory** do Flask, organizado da seguinte forma:

```
StudentManagementSystem/
├── student_system/          # Pacote principal da aplicação
│   ├── __init__.py         # Factory da aplicação Flask
│   ├── models.py           # Modelos do banco de dados
│   ├── routes.py           # Rotas principais da aplicação
│   ├── auth.py             # Autenticação e autorização
│   ├── static/             # Arquivos estáticos (CSS, JS, imagens)
│   └── templates/          # Templates HTML
├── config.py               # Configurações da aplicação
├── run.py                  # Ponto de entrada principal
├── deploy.py               # Script de deploy para produção
├── migrate_db.py           # Script para migrações do banco
├── requirements.txt        # Dependências do projeto
├── env.example             # Exemplo de variáveis de ambiente
├── instance/               # Arquivos de instância (banco de dados)
├── uploads/                # Arquivos enviados pelos usuários
├── logs/                   # Logs da aplicação
├── backups/                # Backups do banco de dados
└── migrations/             # Migrações do banco de dados
```

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

### Passos de Instalação

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd StudentManagementSystem
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Linux/macOS:**
     ```bash
     source venv/bin/activate
     ```

4. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure as variáveis de ambiente:**
   - Copie o arquivo de exemplo: `cp env.example .env`
   - Edite o arquivo `.env` com suas configurações
   - **IMPORTANTE:** Defina uma `SECRET_KEY` segura

6. **Inicialize o banco de dados:**
   ```bash
   python migrate_db.py init
   python migrate_db.py migrate
   python migrate_db.py upgrade
   ```

7. **Execute a aplicação:**
   ```bash
   python run.py
   ```

A aplicação estará disponível em:
- **Local:** http://127.0.0.1:5000
- **Rede:** http://[seu-ip]:5000

### Credenciais Padrão

- **Usuário:** admin
- **Senha:** admin

⚠️ **Importante:** Altere a senha do administrador após o primeiro login!

## 🚀 Deploy para Produção

### Deploy Automático

Execute o script de deploy:
```bash
python deploy.py
```

Este script irá:
- Verificar requisitos do sistema
- Configurar ambiente de produção
- Instalar dependências
- Configurar banco de dados
- Criar configuração do Gunicorn
- Gerar arquivo de serviço systemd

### Deploy Manual

1. **Configure o ambiente:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=sua-chave-secreta-muito-segura
   ```

2. **Instale dependências de produção:**
   ```bash
   pip install gunicorn flask-talisman flask-limiter
   ```

3. **Configure o banco de dados:**
   ```bash
   python migrate_db.py upgrade
   ```

4. **Execute com Gunicorn:**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

### Configuração com Nginx

Crie um arquivo de configuração do Nginx:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /caminho/para/StudentManagementSystem/student_system/static;
        expires 30d;
    }
}
```

### Configuração de HTTPS

1. **Instale Certbot:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

2. **Obtenha certificado SSL:**
   ```bash
   sudo certbot --nginx -d seu-dominio.com
   ```

### Backup Automático

Configure backup automático do banco de dados:

```bash
# Adicione ao crontab
0 2 * * * /usr/bin/python3 /caminho/para/StudentManagementSystem/backup_db.py
```

## 📋 Funcionalidades

### 👥 Gerenciamento de Alunos
- Cadastro, edição e exclusão de alunos
- Informações pessoais e de contato
- Associação a tipos de aula
- Links diretos para WhatsApp

### 💰 Controle de Mensalidades
- Registro de pagamentos por mês/ano
- Status de pagamento (Pago/Pendente)
- Recebimento de pagamentos
- Relatórios financeiros

### 📚 Tipos de Aula
- Configuração de diferentes modalidades
- Preços padrão por tipo
- Descrições detalhadas

### 📢 Sistema de Notificações
- Envio individual ou em grupo
- Integração com WhatsApp
- Histórico de notificações enviadas
- Diferentes tipos: Cobrança, Lembrete, Aviso

### 📁 Gerenciamento de Arquivos
- Upload de documentos, imagens, áudios e vídeos
- Organização por aluno ou tipo de aula
- Download e compartilhamento via WhatsApp
- Suporte a múltiplos formatos

### 📊 Dashboard
- Visão geral dos pagamentos
- Gráficos de receita mensal
- Filtros por período e tipo de aula
- Exportação para Excel e PDF

## 🛠️ Tecnologias Utilizadas

- **Backend:** Flask 3.0.3
- **Banco de Dados:** SQLite (SQLAlchemy)
- **Autenticação:** Flask-Login
- **Migrações:** Flask-Migrate (Alembic)
- **Relatórios:** ReportLab, OpenPyXL
- **Gráficos:** Matplotlib
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Produção:** Gunicorn, Nginx

## 🔒 Segurança

### Configurações Implementadas
- Autenticação obrigatória para todas as rotas
- Senhas criptografadas com Werkzeug
- Proteção contra CSRF
- Validação de arquivos enviados
- Configuração de chave secreta via variável de ambiente
- Headers de segurança HTTP
- Rate limiting para proteção contra ataques
- Sessões seguras com cookies HTTPOnly

### Recomendações Adicionais
- Configure HTTPS obrigatório
- Implemente autenticação de dois fatores
- Configure firewall adequadamente
- Monitore logs de acesso
- Faça backup regular dos dados
- Mantenha dependências atualizadas

## 🔧 Comandos Úteis

### Migrações do Banco de Dados
```bash
# Inicializar migrações
python migrate_db.py init

# Criar nova migração
python migrate_db.py migrate "descrição da mudança"

# Aplicar migrações pendentes
python migrate_db.py upgrade
```

### Execução da Aplicação
```bash
# Modo desenvolvimento
python run.py

# Modo produção com Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# Modo produção com configuração personalizada
gunicorn -c gunicorn.conf.py run:app
```

### Monitoramento
```bash
# Verificar logs da aplicação
tail -f logs/student_system.log

# Verificar logs do Gunicorn
tail -f logs/gunicorn_access.log
tail -f logs/gunicorn_error.log

# Verificar status do serviço (se configurado)
sudo systemctl status student-management
```

## 📁 Estrutura de Arquivos

### Configurações (`config.py`)
- Chave secreta da aplicação
- Configuração do banco de dados
- Diretórios de upload
- Configurações de segurança

### Modelos (`student_system/models.py`)
- **User:** Usuários do sistema
- **Student:** Alunos cadastrados
- **LessonType:** Tipos de aula
- **Payment:** Pagamentos/mensalidades
- **Notification:** Notificações enviadas
- **File:** Arquivos enviados

### Rotas (`student_system/routes.py`)
- Dashboard e relatórios
- CRUD de alunos
- CRUD de tipos de aula
- CRUD de pagamentos
- CRUD de notificações
- Gerenciamento de arquivos

### Autenticação (`student_system/auth.py`)
- Login/logout
- Alteração de senha
- Proteção de rotas

## 🚀 Deploy

### Checklist de Produção

- [ ] SECRET_KEY configurada e segura
- [ ] FLASK_ENV=production
- [ ] HTTPS configurado
- [ ] Firewall configurado
- [ ] Backup automático configurado
- [ ] Monitoramento configurado
- [ ] Logs configurados
- [ ] Senha do administrador alterada
- [ ] Dependências atualizadas
- [ ] Testes realizados

### Variáveis de Ambiente Obrigatórias

```env
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta-muito-segura
DATABASE_URL=sqlite:///instance/app.db
LOG_LEVEL=WARNING
```

## 📞 Suporte

Para suporte técnico ou dúvidas sobre o sistema, consulte a documentação ou entre em contato com a equipe de desenvolvimento.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🔐 Redefinição de Senha

### Métodos Disponíveis

#### 1. **Via Interface Web (Desenvolvimento)**
- Acesse: `http://127.0.0.1:5000/forgot_password`
- Digite o nome de usuário
- O código será exibido na tela (apenas desenvolvimento)
- Use o código para redefinir a senha

#### 2. **Via Linha de Comando (Recomendado para Produção)**
```bash
python reset_admin_password.py
```
Este script oferece:
- Geração de senha aleatória segura
- Definição manual de senha
- Confirmação antes da redefinição
- Validação de segurança

#### 3. **Via Email (Opcional)**
Para configurar redefinição via email:
```bash
# Configurar variáveis de email
python email_reset.py --setup

# Testar configuração
python email_reset.py --test
```

### Redefinição Especial do Administrador
Se você esqueceu a senha do administrador e não consegue acessar o sistema:

1. **Via linha de comando (mais seguro):**
   ```bash
   python reset_admin_password.py
   ```

2. **Via interface web (apenas desenvolvimento):**
   - Acesse: `http://127.0.0.1:5000/admin_reset`
   - Use a chave secreta: `admin_reset_2025`
   - ⚠️ **IMPORTANTE:** Esta funcionalidade é apenas para desenvolvimento

### Segurança

- **Desenvolvimento:** Códigos exibidos na tela
- **Produção:** Use linha de comando ou email
- **Tokens:** Expiram em 15 minutos
- **Senhas:** Mínimo 6 caracteres
- **Validação:** Confirmação obrigatória

## 🚀 Deploy para Produção
