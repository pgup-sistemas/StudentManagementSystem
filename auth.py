# auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User  # Importação absoluta
from __init__ import db  # Importação absoluta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
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

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change_password', methods=['POST'])
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
    
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    flash('Senha alterada com sucesso.', 'success')
    return redirect(url_for('main.dashboard'))