# 🎵 Sonaris - Sistema de Gerenciamento de Escola de Música

Sistema Sonaris - Solução completa para gerenciamento de escolas de música, desenvolvido com Python e Flask. Gerencie alunos, pagamentos, aulas e muito mais em uma interface intuitiva.

## ✨ Funcionalidades Principais

- 👥 **Gerenciamento de Alunos** - Cadastro completo com informações pessoais e de contato
- 💰 **Controle Financeiro** - Acompanhamento de pagamentos e mensalidades
- 📅 **Agenda de Aulas** - Agendamento e acompanhamento de aulas
- 📁 **Armazenamento de Arquivos** - Armazene partituras, áudios e vídeos (até 10MB por arquivo)
- 🔔 **Sistema de Notificações** - Mantenha contato com alunos e responsáveis
- 📊 **Relatórios** - Visualize métricas importantes em tempo real

## 🚀 Começando Rápido

### Pré-requisitos
- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Navegador moderno (Chrome, Firefox, Edge, etc.)

### Instalação Rápida

1. **Clone o repositório**
   ```bash
   git clone https://github.com/pgup-sistemas/StudentManagementSystem.git
   cd StudentManagementSystem
   ```

2. **Configure o ambiente virtual**
   ```bash
   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -e .
   ```

4. **Configure o ambiente** (opcional)
   Crie um arquivo `.env` na raiz com:
   ```
   FLASK_APP=main.py
   FLASK_ENV=development
   SECRET_KEY=crie_sua_chave_secreta_aqui
   DATABASE_URL=sqlite:///music_school.db
   ```

5. **Inicie o servidor**
   ```bash
   flask run
   ```

6. **Acesse o sistema**
   Abra seu navegador em:
   ```
   http://localhost:5000
   ```

7. **Primeiro acesso**
   - **Usuário:** admin
   - **Senha:** admin
   
   ⚠️ **Importante:** Altere a senha padrão no primeiro acesso!

## 🛠️ Estrutura do Projeto

```
StudentManagementSystem/
├── app.py              # Configuração principal do Flask
├── models.py           # Modelos do banco de dados
├── routes.py           # Rotas da aplicação
├── auth.py             # Autenticação e autorização
├── static/             # Arquivos estáticos (CSS, JS, imagens)
│   └── uploads/       # Arquivos enviados pelos usuários
├── templates/          # Templates HTML
└── instance/           # Banco de dados SQLite (criado automaticamente)
```

## 🔧 Comandos Úteis

| Comando | Descrição |
|---------|-----------|
| `flask run` | Inicia o servidor de desenvolvimento |
| `flask shell` | Abre o shell interativo do Flask |
| `flask db migrate -m "mensagem"` | Cria uma nova migração |
| `flask db upgrade` | Aplica as migrações pendentes |

## 🚨 Solução de Problemas

### Erro de Módulo Não Encontrado
```bash
pip install flask flask-sqlalchemy flask-login werkzeug
```

### Porta 5000 em Uso
```bash
flask run --port 5001
```

### Reset do Banco de Dados
⚠️ **Atenção:** Isso apagará todos os dados!
```bash
rm instance/music_school.db
flask run  # O banco será recriado automaticamente
```

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estes passos:

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Adicione suas mudanças (`git add .`)
4. Comite suas mudanças (`git commit -m 'Add some AmazingFeature'`)
5. Faça o Push da Branch (`git push origin feature/AmazingFeature`)
6. Abra um Pull Request

## 📞 Suporte

Para suporte, entre em contato:
- Email: [pageupsistemas@gmail.com](mailto:pageupsistemas@gmail.com)
- Issues: [Abrir uma Issue](https://github.com/pgup-sistemas/StudentManagementSystem/issues)

---

Desenvolvido com ❤️ por [PageUp Sistemas](https://github.com/pgup-sistemas) - Transformando educação musical através da tecnologia
