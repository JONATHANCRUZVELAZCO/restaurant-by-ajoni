from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Comanda, DetalleComanda, Mesa, Producto, get_mexico_time
from app.auth import role_required
from sqlalchemy import desc

comandas_bp = Blueprint('comandas', __name__)

@comandas_bp.route('/')
@login_required
def listar():
    """Listar comandas según el rol del usuario"""
    if current_user.rol == 'cocina':
        # Cocina solo ve comandas pendientes y en preparación
        comandas = Comanda.query.filter(
            Comanda.estado.in_(['pendiente', 'en_preparacion'])
        ).order_by(Comanda.fecha_creacion).all()
        return render_template('comandas/cocina.html', comandas=comandas)
    
    elif current_user.rol == 'mesero':
        # Mesero ve sus propias comandas del día
        comandas = Comanda.query.filter_by(
            mesero_id=current_user.id
        ).order_by(desc(Comanda.fecha_creacion)).limit(50).all()
        return render_template('comandas/listar.html', comandas=comandas)
    
    else:
        # Admin y caja ven todas las comandas
        page = request.args.get('page', 1, type=int)
        estado = request.args.get('estado')
        
        query = Comanda.query
        if estado:
            query = query.filter_by(estado=estado)
        
        comandas = query.order_by(desc(Comanda.fecha_creacion)).paginate(
            page=page, per_page=20, error_out=False
        )
        return render_template('comandas/listar.html', comandas=comandas)

@comandas_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'mesero')
def crear():
    """Crear una nueva comanda"""
    if request.method == 'POST':
        mesa_id = request.form.get('mesa_id', type=int)
        observaciones = request.form.get('observaciones')
        
        if not mesa_id:
            flash('Debes seleccionar una mesa.', 'warning')
            return redirect(url_for('comandas.crear'))
        
        mesa = Mesa.query.get_or_404(mesa_id)
        
        # Verificar que la mesa no tenga una comanda activa
        comanda_activa = Comanda.query.filter_by(mesa_id=mesa_id).filter(
            Comanda.estado.in_(['pendiente', 'en_preparacion', 'lista'])
        ).first()
        
        if comanda_activa:
            flash(f'La mesa {mesa.numero} ya tiene una comanda activa.', 'danger')
            return redirect(url_for('comandas.crear'))
        
        # Crear la comanda
        nueva_comanda = Comanda(
            mesa_id=mesa_id,
            mesero_id=current_user.id,
            estado='pendiente',
            observaciones=observaciones
        )
        
        try:
            db.session.add(nueva_comanda)
            db.session.commit()
            
            # Cambiar estado de la mesa
            mesa.estado = 'ocupada'
            db.session.commit()
            
            flash(f'Comanda creada exitosamente para la mesa {mesa.numero}.', 'success')
            return redirect(url_for('comandas.editar', id=nueva_comanda.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la comanda: {str(e)}', 'danger')
    
    # Obtener mesas disponibles
    mesas = Mesa.query.filter_by(estado='disponible').order_by(Mesa.numero).all()
    return render_template('comandas/crear.html', mesas=mesas)

@comandas_bp.route('/<int:id>')
@login_required
def ver(id):
    """Ver detalles de una comanda"""
    comanda = Comanda.query.get_or_404(id)
    
    # Verificar permisos
    if current_user.rol == 'mesero' and comanda.mesero_id != current_user.id:
        flash('No tienes permiso para ver esta comanda.', 'danger')
        return redirect(url_for('comandas.listar'))
    
    return render_template('comandas/ver.html', comanda=comanda)

@comandas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'mesero')
def editar(id):
    """Editar una comanda (agregar/quitar productos)"""
    comanda = Comanda.query.get_or_404(id)
    
    # Verificar permisos
    if current_user.rol == 'mesero' and comanda.mesero_id != current_user.id:
        flash('No tienes permiso para editar esta comanda.', 'danger')
        return redirect(url_for('comandas.listar'))
    
    # No se puede editar si ya está pagada o entregada
    if comanda.estado in ['entregada', 'cancelada']:
        flash('No se puede editar una comanda entregada o cancelada.', 'warning')
        return redirect(url_for('comandas.ver', id=id))
    
    if request.method == 'POST':
        producto_id = request.form.get('producto_id', type=int)
        cantidad = request.form.get('cantidad', type=int)
        observaciones = request.form.get('observaciones_item')
        
        if not producto_id or not cantidad or cantidad <= 0:
            flash('Datos inválidos.', 'warning')
            return redirect(url_for('comandas.editar', id=id))
        
        producto = Producto.query.get_or_404(producto_id)
        
        if not producto.disponible:
            flash(f'El producto {producto.nombre} no está disponible.', 'danger')
            return redirect(url_for('comandas.editar', id=id))
        
        # Crear detalle de comanda
        detalle = DetalleComanda(
            comanda_id=comanda.id,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=producto.precio,
            observaciones=observaciones
        )
        detalle.calcular_subtotal()
        
        try:
            db.session.add(detalle)
            comanda.calcular_totales()
            db.session.commit()
            flash(f'{producto.nombre} agregado a la comanda.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar el producto: {str(e)}', 'danger')
        
        return redirect(url_for('comandas.editar', id=id))
    
    # Obtener productos disponibles por categoría
    from app.models import Categoria
    categorias = Categoria.query.filter_by(activo=True).all()
    
    return render_template('comandas/editar.html', comanda=comanda, categorias=categorias)

@comandas_bp.route('/detalle/<int:id>/eliminar', methods=['POST'])
@login_required
@role_required('admin', 'mesero')
def eliminar_detalle(id):
    """Eliminar un producto de la comanda"""
    detalle = DetalleComanda.query.get_or_404(id)
    comanda = detalle.comanda
    
    # Verificar permisos
    if current_user.rol == 'mesero' and comanda.mesero_id != current_user.id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    if comanda.estado in ['entregada', 'cancelada']:
        return jsonify({'success': False, 'message': 'Comanda no editable'}), 400
    
    try:
        db.session.delete(detalle)
        comanda.calcular_totales()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Producto eliminado'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@comandas_bp.route('/<int:id>/cambiar-estado', methods=['POST'])
@login_required
def cambiar_estado(id):
    """Cambiar el estado de una comanda"""
    comanda = Comanda.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')
    
    estados_validos = ['pendiente', 'en_preparacion', 'lista', 'entregada', 'cancelada']
    if nuevo_estado not in estados_validos:
        return jsonify({'success': False, 'message': 'Estado inválido'}), 400
    
    # Validar transiciones de estado según el rol
    if current_user.rol == 'cocina':
        # Cocina puede cambiar: pendiente -> en_preparacion -> lista
        if nuevo_estado not in ['en_preparacion', 'lista']:
            return jsonify({'success': False, 'message': 'Transición no permitida'}), 403
    
    elif current_user.rol == 'mesero':
        # Mesero puede cambiar: lista -> entregada o cualquiera -> cancelada
        if nuevo_estado not in ['entregada', 'cancelada']:
            return jsonify({'success': False, 'message': 'Transición no permitida'}), 403
    
    comanda.estado = nuevo_estado
    comanda.fecha_actualizacion = get_mexico_time()
    
    # Si se entrega o cancela, liberar la mesa
    if nuevo_estado in ['entregada', 'cancelada']:
        comanda.mesa.estado = 'limpieza'
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Estado actualizado a {nuevo_estado}',
            'estado': nuevo_estado
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@comandas_bp.route('/<int:id>/cancelar', methods=['POST'])
@login_required
@role_required('admin', 'mesero')
def cancelar(id):
    """Cancelar una comanda"""
    comanda = Comanda.query.get_or_404(id)
    
    # Verificar permisos
    if current_user.rol == 'mesero' and comanda.mesero_id != current_user.id:
        flash('No tienes permiso para cancelar esta comanda.', 'danger')
        return redirect(url_for('comandas.listar'))
    
    if comanda.estado == 'entregada':
        flash('No se puede cancelar una comanda ya entregada.', 'danger')
        return redirect(url_for('comandas.ver', id=id))
    
    comanda.estado = 'cancelada'
    comanda.mesa.estado = 'limpieza'
    
    try:
        db.session.commit()
        flash('Comanda cancelada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cancelar la comanda: {str(e)}', 'danger')
    
    return redirect(url_for('comandas.listar'))

@comandas_bp.route('/api/activas')
@login_required
@role_required('cocina')
def api_activas():
    """API para obtener comandas activas (para cocina)"""
    comandas = Comanda.query.filter(
        Comanda.estado.in_(['pendiente', 'en_preparacion'])
    ).order_by(Comanda.fecha_creacion).all()
    
    return jsonify([{
        'id': c.id,
        'mesa': c.mesa.numero,
        'estado': c.estado,
        'mesero': c.mesero.nombre,
        'tiempo': str(c.fecha_creacion),
        'detalles': [{
            'producto': d.producto.nombre,
            'cantidad': d.cantidad,
            'observaciones': d.observaciones
        } for d in c.detalles]
    } for c in comandas])