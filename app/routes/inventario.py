from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.models import db, Producto, Categoria
from app.auth import role_required
from sqlalchemy import or_

inventario_bp = Blueprint('inventario', __name__)

# ============ CATEGORÍAS ============

@inventario_bp.route('/categorias')
@login_required
@role_required('admin')
def categorias():
    """Listar todas las categorías"""
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('inventario/categorias.html', categorias=categorias)

@inventario_bp.route('/categorias/crear', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def crear_categoria():
    """Crear una nueva categoría"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        
        if not nombre:
            flash('El nombre de la categoría es obligatorio.', 'warning')
            return render_template('inventario/crear_categoria.html')
        
        # Verificar que no exista
        if Categoria.query.filter_by(nombre=nombre).first():
            flash(f'Ya existe una categoría con el nombre "{nombre}".', 'danger')
            return render_template('inventario/crear_categoria.html')
        
        nueva_categoria = Categoria(
            nombre=nombre,
            descripcion=descripcion
        )
        
        try:
            db.session.add(nueva_categoria)
            db.session.commit()
            flash(f'Categoría "{nombre}" creada exitosamente.', 'success')
            return redirect(url_for('inventario.categorias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la categoría: {str(e)}', 'danger')
    
    return render_template('inventario/crear_categoria.html')

@inventario_bp.route('/categorias/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_categoria(id):
    """Editar una categoría"""
    categoria = Categoria.query.get_or_404(id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        activo = request.form.get('activo') == 'on'
        
        # Verificar nombre único
        cat_existente = Categoria.query.filter_by(nombre=nombre).first()
        if cat_existente and cat_existente.id != id:
            flash(f'Ya existe otra categoría con el nombre "{nombre}".', 'danger')
            return render_template('inventario/editar_categoria.html', categoria=categoria)
        
        categoria.nombre = nombre
        categoria.descripcion = descripcion
        categoria.activo = activo
        
        try:
            db.session.commit()
            flash(f'Categoría "{nombre}" actualizada exitosamente.', 'success')
            return redirect(url_for('inventario.categorias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la categoría: {str(e)}', 'danger')
    
    return render_template('inventario/editar_categoria.html', categoria=categoria)

@inventario_bp.route('/categorias/<int:id>/eliminar', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_categoria(id):
    """Eliminar una categoría"""
    categoria = Categoria.query.get_or_404(id)
    
    # Verificar que no tenga productos
    if categoria.productos:
        flash('No se puede eliminar la categoría porque tiene productos asociados.', 'danger')
        return redirect(url_for('inventario.categorias'))
    
    try:
        db.session.delete(categoria)
        db.session.commit()
        flash(f'Categoría "{categoria.nombre}" eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la categoría: {str(e)}', 'danger')
    
    return redirect(url_for('inventario.categorias'))

# ============ PRODUCTOS ============

@inventario_bp.route('/')
@login_required
@role_required('admin', 'mesero')
def productos():
    """Listar todos los productos"""
    # Filtros
    buscar = request.args.get('buscar', '')
    categoria_id = request.args.get('categoria', type=int)
    disponible = request.args.get('disponible')
    alerta_stock = request.args.get('alerta_stock')
    
    query = Producto.query
    
    if buscar:
        query = query.filter(
            or_(
                Producto.nombre.ilike(f'%{buscar}%'),
                Producto.descripcion.ilike(f'%{buscar}%')
            )
        )
    
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    
    if disponible == 'si':
        query = query.filter_by(disponible=True)
    elif disponible == 'no':
        query = query.filter_by(disponible=False)
    
    if alerta_stock == 'si':
        query = query.filter(Producto.stock <= Producto.stock_minimo)
    
    productos = query.order_by(Producto.nombre).all()
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    
    return render_template('inventario/productos.html', 
                         productos=productos, 
                         categorias=categorias)

@inventario_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def crear_producto():
    """Crear un nuevo producto"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio', type=float)
        categoria_id = request.form.get('categoria_id', type=int)
        stock = request.form.get('stock', type=int, default=0)
        stock_minimo = request.form.get('stock_minimo', type=int, default=5)
        disponible = request.form.get('disponible') == 'on'
        
        if not nombre or not precio or not categoria_id:
            flash('Nombre, precio y categoría son obligatorios.', 'warning')
            categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
            return render_template('inventario/crear_producto.html', categorias=categorias)
        
        if precio <= 0:
            flash('El precio debe ser mayor a cero.', 'warning')
            categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
            return render_template('inventario/crear_producto.html', categorias=categorias)
        
        nuevo_producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            categoria_id=categoria_id,
            stock=stock,
            stock_minimo=stock_minimo,
            disponible=disponible
        )
        
        try:
            db.session.add(nuevo_producto)
            db.session.commit()
            flash(f'Producto "{nombre}" creado exitosamente.', 'success')
            return redirect(url_for('inventario.productos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el producto: {str(e)}', 'danger')
    
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    return render_template('inventario/crear_producto.html', categorias=categorias)

@inventario_bp.route('/<int:id>')
@login_required
@role_required('admin', 'mesero')
def ver_producto(id):
    """Ver detalles de un producto"""
    producto = Producto.query.get_or_404(id)
    return render_template('inventario/ver_producto.html', producto=producto)

@inventario_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editar_producto(id):
    """Editar un producto"""
    producto = Producto.query.get_or_404(id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio', type=float)
        categoria_id = request.form.get('categoria_id', type=int)
        stock = request.form.get('stock', type=int)
        stock_minimo = request.form.get('stock_minimo', type=int)
        disponible = request.form.get('disponible') == 'on'
        
        if not nombre or not precio or not categoria_id:
            flash('Nombre, precio y categoría son obligatorios.', 'warning')
            categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
            return render_template('inventario/editar_producto.html', 
                                 producto=producto, 
                                 categorias=categorias)
        
        if precio <= 0:
            flash('El precio debe ser mayor a cero.', 'warning')
            categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
            return render_template('inventario/editar_producto.html', 
                                 producto=producto, 
                                 categorias=categorias)
        
        producto.nombre = nombre
        producto.descripcion = descripcion
        producto.precio = precio
        producto.categoria_id = categoria_id
        producto.stock = stock
        producto.stock_minimo = stock_minimo
        producto.disponible = disponible
        
        try:
            db.session.commit()
            flash(f'Producto "{nombre}" actualizado exitosamente.', 'success')
            return redirect(url_for('inventario.productos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el producto: {str(e)}', 'danger')
    
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    return render_template('inventario/editar_producto.html', 
                         producto=producto, 
                         categorias=categorias)

@inventario_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_producto(id):
    """Eliminar un producto"""
    producto = Producto.query.get_or_404(id)
    
    # Verificar que no tenga ventas asociadas
    if producto.detalles_comanda:
        flash('No se puede eliminar el producto porque tiene ventas asociadas.', 'danger')
        return redirect(url_for('inventario.productos'))
    
    try:
        db.session.delete(producto)
        db.session.commit()
        flash(f'Producto "{producto.nombre}" eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el producto: {str(e)}', 'danger')
    
    return redirect(url_for('inventario.productos'))

@inventario_bp.route('/<int:id>/ajustar-stock', methods=['POST'])
@login_required
@role_required('admin')
def ajustar_stock(id):
    """Ajustar el stock de un producto"""
    producto = Producto.query.get_or_404(id)
    
    accion = request.form.get('accion')  # 'agregar' o 'reducir'
    cantidad = request.form.get('cantidad', type=int)
    
    if not cantidad or cantidad <= 0:
        return jsonify({'success': False, 'message': 'Cantidad inválida'}), 400
    
    if accion == 'agregar':
        producto.stock += cantidad
        mensaje = f'Se agregaron {cantidad} unidades'
    elif accion == 'reducir':
        if producto.stock < cantidad:
            return jsonify({
                'success': False, 
                'message': 'No hay suficiente stock'
            }), 400
        producto.stock -= cantidad
        mensaje = f'Se redujeron {cantidad} unidades'
    else:
        return jsonify({'success': False, 'message': 'Acción inválida'}), 400
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': mensaje,
            'stock_actual': producto.stock,
            'alerta': producto.necesita_reabastecimiento
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@inventario_bp.route('/alertas-stock')
@login_required
@role_required('admin')
def alertas_stock():
    """Ver productos con stock bajo"""
    productos = Producto.query.filter(
        Producto.stock <= Producto.stock_minimo
    ).order_by(Producto.stock).all()
    
    return render_template('inventario/alertas_stock.html', productos=productos)

@inventario_bp.route('/api/productos/<int:categoria_id>')
@login_required
def api_productos_por_categoria(categoria_id):
    """API para obtener productos por categoría"""
    productos = Producto.query.filter_by(
        categoria_id=categoria_id,
        disponible=True
    ).all()
    
    return jsonify([{
        'id': p.id,
        'nombre': p.nombre,
        'descripcion': p.descripcion,
        'precio': float(p.precio),
        'stock': p.stock
    } for p in productos])