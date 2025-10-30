from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Mesa, Comanda
from app.auth import role_required

mesas_bp = Blueprint('mesas', __name__)

@mesas_bp.route('/')
@login_required
@role_required('admin', 'mesero', 'caja')
def listar():
    """Listar todas las mesas"""
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return render_template('mesas/listar.html', mesas=mesas)

@mesas_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def crear():
    """Crear una nueva mesa"""
    if request.method == 'POST':
        numero = request.form.get('numero', type=int)
        capacidad = request.form.get('capacidad', type=int)
        ubicacion = request.form.get('ubicacion')
        
        if not numero or not capacidad:
            flash('El número y capacidad de la mesa son obligatorios.', 'warning')
            return render_template('mesas/crear.html')
        
        # Verificar que no exista una mesa con ese número
        if Mesa.query.filter_by(numero=numero).first():
            flash(f'Ya existe una mesa con el número {numero}.', 'danger')
            return render_template('mesas/crear.html')
        
        nueva_mesa = Mesa(
            numero=numero,
            capacidad=capacidad,
            ubicacion=ubicacion,
            estado='disponible'
        )
        
        try:
            db.session.add(nueva_mesa)
            db.session.commit()
            flash(f'Mesa {numero} creada exitosamente.', 'success')
            return redirect(url_for('mesas.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la mesa: {str(e)}', 'danger')
    
    return render_template('mesas/crear.html')

@mesas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar(id):
    """Editar una mesa existente"""
    mesa = Mesa.query.get_or_404(id)
    
    if request.method == 'POST':
        numero = request.form.get('numero', type=int)
        capacidad = request.form.get('capacidad', type=int)
        ubicacion = request.form.get('ubicacion')
        estado = request.form.get('estado')
        
        # Verificar que no exista otra mesa con ese número
        mesa_existente = Mesa.query.filter_by(numero=numero).first()
        if mesa_existente and mesa_existente.id != id:
            flash(f'Ya existe otra mesa con el número {numero}.', 'danger')
            return render_template('mesas/editar.html', mesa=mesa)
        
        mesa.numero = numero
        mesa.capacidad = capacidad
        mesa.ubicacion = ubicacion
        mesa.estado = estado
        
        try:
            db.session.commit()
            flash(f'Mesa {numero} actualizada exitosamente.', 'success')
            return redirect(url_for('mesas.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la mesa: {str(e)}', 'danger')
    
    return render_template('mesas/editar.html', mesa=mesa)

@mesas_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@role_required('admin')
def eliminar(id):
    """Eliminar una mesa"""
    mesa = Mesa.query.get_or_404(id)
    
    # Verificar que no tenga comandas activas
    comandas_activas = Comanda.query.filter_by(mesa_id=id).filter(
        Comanda.estado.in_(['pendiente', 'en_preparacion', 'lista'])
    ).count()
    
    if comandas_activas > 0:
        flash('No se puede eliminar la mesa porque tiene comandas activas.', 'danger')
        return redirect(url_for('mesas.listar'))
    
    try:
        db.session.delete(mesa)
        db.session.commit()
        flash(f'Mesa {mesa.numero} eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la mesa: {str(e)}', 'danger')
    
    return redirect(url_for('mesas.listar'))

@mesas_bp.route('/<int:id>/cambiar-estado', methods=['POST'])
@login_required
@role_required('admin', 'mesero')
def cambiar_estado(id):
    """Cambiar el estado de una mesa"""
    mesa = Mesa.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')
    
    estados_validos = ['disponible', 'ocupada', 'reservada', 'limpieza']
    if nuevo_estado not in estados_validos:
        return jsonify({'success': False, 'message': 'Estado inválido'}), 400
    
    mesa.estado = nuevo_estado
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Estado de mesa {mesa.numero} actualizado',
            'estado': nuevo_estado
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@mesas_bp.route('/mapa')
@login_required
@role_required('admin', 'mesero', 'caja')
def mapa():
    """Vista de mapa de mesas con estado en tiempo real"""
    mesas = Mesa.query.order_by(Mesa.numero).all()
    
    # Agregar información de comandas activas
    for mesa in mesas:
        mesa.comanda_activa = Comanda.query.filter_by(
            mesa_id=mesa.id
        ).filter(
            Comanda.estado.in_(['pendiente', 'en_preparacion', 'lista'])
        ).first()
    
    return render_template('mesas/mapa.html', mesas=mesas)

@mesas_bp.route('/api/estado')
@login_required
def api_estado():
    """API para obtener el estado de todas las mesas"""
    mesas = Mesa.query.all()
    return jsonify([{
        'id': m.id,
        'numero': m.numero,
        'estado': m.estado,
        'capacidad': m.capacidad,
        'ubicacion': m.ubicacion
    } for m in mesas])