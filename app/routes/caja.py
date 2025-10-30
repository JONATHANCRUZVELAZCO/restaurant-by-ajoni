from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Turno, Pago, Comanda, Mesa, get_mexico_time
from app.auth import role_required
from sqlalchemy import func, desc
from datetime import datetime, timedelta

caja_bp = Blueprint('caja', __name__)

@caja_bp.route('/')
@login_required
@role_required('admin', 'caja')
def index():
    """Página principal de caja"""
    # Verificar si hay un turno abierto
    turno_activo = Turno.query.filter_by(
        usuario_id=current_user.id,
        estado='abierto'
    ).first()
    
    if turno_activo:
        # Calcular ventas del turno
        ventas = {
            'efectivo': turno_activo.calcular_ventas_efectivo(),
            'tarjeta': turno_activo.calcular_ventas_tarjeta(),
            'transferencia': turno_activo.calcular_ventas_transferencia(),
            'total': turno_activo.calcular_total_ventas()
        }
        
        # Comandas pendientes de pago
        comandas_pendientes = Comanda.query.filter_by(
            estado='entregada'
        ).filter(
            ~Comanda.pago.has()
        ).order_by(Comanda.fecha_actualizacion).all()
        
        return render_template('caja/turno_activo.html', 
                             turno=turno_activo, 
                             ventas=ventas,
                             comandas_pendientes=comandas_pendientes)
    else:
        return render_template('caja/sin_turno.html')

@caja_bp.route('/abrir-turno', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'caja')
def abrir_turno():
    """Abrir un nuevo turno de caja"""
    # Verificar que no haya un turno abierto
    turno_activo = Turno.query.filter_by(
        usuario_id=current_user.id,
        estado='abierto'
    ).first()
    
    if turno_activo:
        flash('Ya tienes un turno abierto.', 'warning')
        return redirect(url_for('caja.index'))
    
    if request.method == 'POST':
        monto_inicial = request.form.get('monto_inicial', type=float)
        observaciones = request.form.get('observaciones')
        
        if monto_inicial is None or monto_inicial < 0:
            flash('El monto inicial debe ser mayor o igual a cero.', 'warning')
            return render_template('caja/abrir_turno.html')
        
        nuevo_turno = Turno(
            usuario_id=current_user.id,
            monto_inicial=monto_inicial,
            observaciones=observaciones,
            estado='abierto'
        )
        
        try:
            db.session.add(nuevo_turno)
            db.session.commit()
            flash(f'Turno abierto exitosamente con ${monto_inicial:.2f}', 'success')
            return redirect(url_for('caja.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al abrir el turno: {str(e)}', 'danger')
    
    return render_template('caja/abrir_turno.html')

@caja_bp.route('/cerrar-turno', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'caja')
def cerrar_turno():
    """Cerrar el turno de caja actual"""
    turno = Turno.query.filter_by(
        usuario_id=current_user.id,
        estado='abierto'
    ).first()
    
    if not turno:
        flash('No tienes un turno abierto.', 'warning')
        return redirect(url_for('caja.index'))
    
    # Verificar comandas sin pagar
    comandas_sin_pagar = Comanda.query.filter_by(
        estado='entregada'
    ).filter(
        ~Comanda.pago.has()
    ).count()
    
    if comandas_sin_pagar > 0:
        flash(f'Hay {comandas_sin_pagar} comandas sin pagar. Procesa los pagos antes de cerrar el turno.', 'warning')
        return redirect(url_for('caja.index'))
    
    if request.method == 'POST':
        monto_final = request.form.get('monto_final', type=float)
        observaciones = request.form.get('observaciones')
        
        if monto_final is None or monto_final < 0:
            flash('El monto final debe ser mayor o igual a cero.', 'warning')
            return redirect(url_for('caja.cerrar_turno'))
        
        turno.monto_final = monto_final
        turno.fecha_cierre = get_mexico_time()
        turno.estado = 'cerrado'
        if observaciones:
            turno.observaciones = f"{turno.observaciones or ''}\nCierre: {observaciones}"
        
        try:
            db.session.commit()
            flash('Turno cerrado exitosamente.', 'success')
            return redirect(url_for('caja.reporte_turno', id=turno.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al cerrar el turno: {str(e)}', 'danger')
    
    # Calcular ventas del turno
    ventas = {
        'efectivo': turno.calcular_ventas_efectivo(),
        'tarjeta': turno.calcular_ventas_tarjeta(),
        'transferencia': turno.calcular_ventas_transferencia(),
        'total': turno.calcular_total_ventas()
    }
    
    return render_template('caja/cerrar_turno.html', turno=turno, ventas=ventas)

@caja_bp.route('/procesar-pago/<int:comanda_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'caja')
def procesar_pago(comanda_id):
    """Procesar el pago de una comanda"""
    comanda = Comanda.query.get_or_404(comanda_id)
    
    # Verificar que la comanda esté entregada y no pagada
    if comanda.estado != 'entregada':
        flash('La comanda debe estar entregada para procesarla.', 'warning')
        return redirect(url_for('caja.index'))
    
    if comanda.pago:
        flash('Esta comanda ya ha sido pagada.', 'warning')
        return redirect(url_for('caja.index'))
    
    # Verificar turno activo
    turno_activo = Turno.query.filter_by(
        usuario_id=current_user.id,
        estado='abierto'
    ).first()
    
    if not turno_activo:
        flash('Debes tener un turno abierto para procesar pagos.', 'danger')
        return redirect(url_for('caja.abrir_turno'))
    
    if request.method == 'POST':
        metodo_pago = request.form.get('metodo_pago')
        monto_recibido = request.form.get('monto_recibido', type=float)
        
        if metodo_pago not in ['Efectivo', 'Tarjeta', 'Transferencia']:
            flash('Método de pago inválido.', 'danger')
            return render_template('caja/procesar_pago.html', comanda=comanda)
        
        # Calcular cambio para efectivo
        cambio = 0
        if metodo_pago == 'Efectivo':
            if not monto_recibido or monto_recibido < float(comanda.total):
                flash('El monto recibido es insuficiente.', 'warning')
                return render_template('caja/procesar_pago.html', comanda=comanda)
            cambio = monto_recibido - float(comanda.total)
        else:
            monto_recibido = float(comanda.total)
        
        # Crear el pago
        pago = Pago(
            comanda_id=comanda.id,
            metodo_pago=metodo_pago,
            monto=comanda.total,
            monto_recibido=monto_recibido,
            cambio=cambio,
            turno_id=turno_activo.id
        )
        
        try:
            db.session.add(pago)
            # Liberar la mesa
            comanda.mesa.estado = 'limpieza'
            db.session.commit()
            
            flash(f'Pago procesado exitosamente. Cambio: ${cambio:.2f}', 'success')
            return redirect(url_for('caja.ticket', id=pago.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar el pago: {str(e)}', 'danger')
    
    return render_template('caja/procesar_pago.html', comanda=comanda)

@caja_bp.route('/ticket/<int:id>')
@login_required
@role_required('admin', 'caja', 'mesero')
def ticket(id):
    """Ver ticket de pago"""
    pago = Pago.query.get_or_404(id)
    return render_template('caja/ticket.html', pago=pago)

@caja_bp.route('/historial-turnos')
@login_required
@role_required('admin', 'caja')
def historial_turnos():
    """Ver historial de turnos"""
    page = request.args.get('page', 1, type=int)
    
    if current_user.rol == 'admin':
        turnos = Turno.query.order_by(desc(Turno.fecha_apertura)).paginate(
            page=page, per_page=20, error_out=False
        )
    else:
        turnos = Turno.query.filter_by(usuario_id=current_user.id).order_by(
            desc(Turno.fecha_apertura)
        ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('caja/historial_turnos.html', turnos=turnos)

@caja_bp.route('/reporte-turno/<int:id>')
@login_required
@role_required('admin', 'caja')
def reporte_turno(id):
    """Ver reporte detallado de un turno"""
    turno = Turno.query.get_or_404(id)
    
    # Verificar permisos
    if current_user.rol == 'caja' and turno.usuario_id != current_user.id:
        flash('No tienes permiso para ver este turno.', 'danger')
        return redirect(url_for('caja.historial_turnos'))
    
    # Calcular estadísticas
    ventas = {
        'efectivo': turno.calcular_ventas_efectivo(),
        'tarjeta': turno.calcular_ventas_tarjeta(),
        'transferencia': turno.calcular_ventas_transferencia(),
        'total': turno.calcular_total_ventas()
    }
    
    # Desglose de pagos
    pagos_detalle = Pago.query.filter_by(turno_id=turno.id).order_by(Pago.fecha_pago).all()
    
    # Diferencia de caja (solo si está cerrado)
    diferencia = None
    if turno.estado == 'cerrado' and turno.monto_final is not None:
        esperado = float(turno.monto_inicial) + float(ventas['efectivo'])
        diferencia = float(turno.monto_final) - esperado
    
    return render_template('caja/reporte_turno.html', 
                         turno=turno, 
                         ventas=ventas,
                         pagos=pagos_detalle,
                         diferencia=diferencia)

@caja_bp.route('/comandas-pendientes')
@login_required
@role_required('admin', 'caja')
def comandas_pendientes():
    """Ver todas las comandas pendientes de pago"""
    comandas = Comanda.query.filter_by(
        estado='entregada'
    ).filter(
        ~Comanda.pago.has()
    ).order_by(Comanda.fecha_actualizacion).all()
    
    return render_template('caja/comandas_pendientes.html', comandas=comandas)