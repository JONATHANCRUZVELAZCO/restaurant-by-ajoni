from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
from config import config
from app.models import db
from app.auth import init_auth, auth_bp

def create_app(config_name='development'):
    """Crear y configurar la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    db.init_app(app)
    init_auth(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Importar y registrar routes
    from app.routes import mesas, comandas, caja, inventario, reportes
    app.register_blueprint(mesas.mesas_bp, url_prefix='/mesas')
    app.register_blueprint(comandas.comandas_bp, url_prefix='/comandas')
    app.register_blueprint(caja.caja_bp, url_prefix='/caja')
    app.register_blueprint(inventario.inventario_bp, url_prefix='/inventario')
    app.register_blueprint(reportes.reportes_bp, url_prefix='/reportes')
    
    # Ruta principal
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('auth.login'))
    
    # Dashboard principal
    @app.route('/dashboard')
    def dashboard():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Redirigir según el rol
        if current_user.rol == 'admin':
            return render_template('dashboard/admin.html')
        elif current_user.rol == 'mesero':
            return render_template('dashboard/mesero.html')
        elif current_user.rol == 'cocina':
            return render_template('dashboard/cocina.html')
        elif current_user.rol == 'caja':
            return render_template('dashboard/caja.html')
        
        return render_template('dashboard/default.html')
    
    # Registrar el blueprint main para el dashboard
    from flask import Blueprint
    main_bp = Blueprint('main', __name__)
    main_bp.add_url_rule('/dashboard', 'dashboard', dashboard)
    app.register_blueprint(main_bp)
    
    # Manejadores de errores
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    # Context processor para hacer disponibles variables globales en templates
    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'Restaurant POS',
            'current_year': 2025
        }
    
    return app