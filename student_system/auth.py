# auth.py
import secrets
import string
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User  # Importação relativa
from . import db  # Importação relativa

bp = Blueprint('auth', __name__)

# Armazenar códigos de redefinição (em produção, usar Redis ou banco de dados)
reset_codes = {}

def generate_reset_code():
    """Gera um código de redefinição de 6 dígitos"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def generate_reset_token():
    """Gera um token seguro para redefinição"""
    return secrets.token_urlsafe(32)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing flash messages
    if '_flashes' in session:
        session['_flashes'].clear()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Por favor, verifique suas credenciais e tente novamente.', 'danger')
            return render_template('login.html')
        
        login_user(user)
        next_page = request.args.get('next')
        
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
        
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Senha atual incorreta.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if new_password != confirm_password:
        flash('As novas senhas não coincidem.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if len(new_password) < 6:
        flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    flash('Senha alterada com sucesso.', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Página para solicitar redefinição de senha"""
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Gerar código de redefinição
            reset_code = generate_reset_code()
            reset_token = generate_reset_token()
            
            # Armazenar código (expira em 15 minutos)
            reset_codes[reset_token] = {
                'user_id': user.id,
                'code': reset_code,
                'expires': datetime.now() + timedelta(minutes=15)
            }
            
            # Em produção, enviar por email
            # Por enquanto, mostrar na tela (apenas desenvolvimento)
            flash(f'Código de redefinição gerado: {reset_code}', 'info')
            
            return redirect(url_for('auth.reset_password', token=reset_token))
        else:
            flash('Usuário não encontrado.', 'danger')
    
    return render_template('forgot_password.html')

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Página para redefinir senha com código"""
    if token not in reset_codes:
        flash('Token inválido ou expirado.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    reset_data = reset_codes[token]
    
    # Verificar se expirou
    if datetime.now() > reset_data['expires']:
        del reset_codes[token]
        flash('Código expirado. Solicite um novo.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        code = request.form.get('code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if code != reset_data['code']:
            flash('Código incorreto.', 'danger')
            return render_template('reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('reset_password.html', token=token)
        
        if len(new_password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('reset_password.html', token=token)
        
        # Atualizar senha
        user = User.query.get(reset_data['user_id'])
        if user:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            # Remover código usado
            del reset_codes[token]
            
            flash('Senha redefinida com sucesso!', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Erro ao redefinir senha.', 'danger')
    
    return render_template('reset_password.html', token=token)

@bp.route('/admin_reset', methods=['GET', 'POST'])
def admin_reset():
    """Redefinição especial para administrador (apenas desenvolvimento)"""
    if request.method == 'POST':
        secret_key = request.form.get('secret_key')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Chave secreta para redefinição (em produção, usar método mais seguro)
        expected_key = "admin_reset_2025"
        
        if secret_key != expected_key:
            flash('Chave secreta incorreta.', 'danger')
            return render_template('admin_reset.html')
        
        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('admin_reset.html')
        
        if len(new_password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('admin_reset.html')
        
        # Atualizar senha do admin
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Senha do administrador redefinida com sucesso!', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Usuário administrador não encontrado.', 'danger')
    
    return render_template('admin_reset.html')