from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from app.models import db, Usuario

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

def init_auth(app):
    """Inicializar el sistema de autenticación"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    """Cargar usuario por ID"""
    return Usuario.query.get(int(user_id))

def role_required(*roles):
    """Decorador para requerir roles específicos"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión primero.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.rol not in roles:
                flash('No tienes permisos para acceder a esta página.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Por favor completa todos los campos.', 'warning')
            return render_template('login.html')
        
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return render_template('login.html')
            
            login_user(usuario, remember=remember)
            flash(f'¡Bienvenido {usuario.nombre}!', 'success')
            
            # Redirigir según el rol
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('main.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Perfil del usuario"""
    return render_template('profile.html')

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('Por favor completa todos los campos.', 'warning')
        return redirect(url_for('auth.profile'))
    
    if not current_user.check_password(current_password):
        flash('La contraseña actual es incorrecta.', 'danger')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('Las contraseñas nuevas no coinciden.', 'danger')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 6:
        flash('La contraseña debe tener al menos 6 caracteres.', 'warning')
        return redirect(url_for('auth.profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Contraseña actualizada exitosamente.', 'success')
    return redirect(url_for('auth.profile'))