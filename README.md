# 🍽️ Restaurant POS - Sistema de Punto de Venta

Sistema completo de Punto de Venta para restaurantes desarrollado con Flask, PostgreSQL y Docker.

## 🚀 Características

### Por Rol de Usuario

#### 👨‍💼 **Administrador**
- Gestión completa de mesas, productos y categorías
- Acceso a todos los reportes y estadísticas
- Control de usuarios y permisos
- Supervisión de turnos de caja

#### 🍽️ **Mesero**
- Gestión de mesas (ocupar, liberar, cambiar estado)
- Crear y editar comandas (pedidos)
- Ver estado de pedidos en cocina
- Consultar tickets

#### 👨‍🍳 **Cocina**
- Ver comandas pendientes y en preparación
- Actualizar estado de platillos
- Vista en tiempo real de pedidos

#### 💰 **Caja**
- Abrir y cerrar turnos
- Procesar pagos (Efectivo, Tarjeta, Transferencia)
- Imprimir tickets
- Control de diferencias de caja

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- Puerto 5000 disponible (aplicación web)
- Puerto 5432 disponible (PostgreSQL)

## 🛠️ Instalación y Configuración

### 1. Clonar o descargar el proyecto

```bash
cd restaurant-pos
```

### 2. Construir y levantar los contenedores

```bash
docker-compose up --build
```

La primera vez que se ejecute, el sistema:
- Creará la base de datos
- Inicializará las tablas
- Cargará datos de prueba

### 3. Acceder al sistema

Abrir el navegador en: **http://localhost:5000**

## 🔐 Credenciales de Acceso

### Administrador
- **Usuario:** admin
- **Contraseña:** admin123

### Mesero
- **Usuario:** mesero1
- **Contraseña:** mesero123

### Cocina
- **Usuario:** cocina
- **Contraseña:** cocina123

### Caja
- **Usuario:** caja
- **Contraseña:** caja123

## 📁 Estructura del Proyecto

```
restaurant-pos/
├── app/
│   ├── __init__.py           # Inicialización de la aplicación
│   ├── models.py             # Modelos de base de datos
│   ├── auth.py               # Sistema de autenticación
│   ├── routes/
│   │   ├── mesas.py          # Rutas para gestión de mesas
│   │   ├── comandas.py       # Rutas para pedidos
│   │   ├── caja.py           # Rutas para pagos y turnos
│   │   ├── inventario.py     # Rutas para productos
│   │   └── reportes.py       # Rutas para reportes
│   ├── templates/            # Plantillas HTML
│   └── static/               # CSS, JS, imágenes
├── config.py                 # Configuración de la aplicación
├── docker-compose.yml        # Orquestación de servicios
├── Dockerfile                # Imagen Docker
├── requirements.txt          # Dependencias Python
├── init_db.py                # Script de inicialización
└── run.py                    # Script principal
```

## 🔄 Flujo de Trabajo Típico

### Para Meseros:
1. **Login** con credenciales de mesero
2. **Seleccionar mesa disponible** desde el mapa de mesas
3. **Crear comanda** para la mesa seleccionada
4. **Agregar productos** a la comanda
5. **Enviar a cocina** (cambiar estado)
6. **Entregar comanda** cuando esté lista
7. **Solicitar pago** en caja

### Para Cocina:
1. **Login** con credenciales de cocina
2. **Ver comandas pendientes** en orden de llegada
3. **Cambiar estado** a "en preparación"
4. **Marcar como "lista"** cuando el platillo esté listo

### Para Caja:
1. **Login** con credenciales de caja
2. **Abrir turno** con monto inicial
3. **Procesar pagos** de comandas entregadas
4. **Cerrar turno** con conteo final
5. **Ver reporte** de diferencias

### Para Administrador:
1. **Login** con credenciales de admin
2. **Acceso completo** a todos los módulos
3. **Ver reportes** de ventas, productos, meseros
4. **Gestionar inventario** y productos
5. **Supervisar operación** en tiempo real

## 📊 Módulos del Sistema

### 1. Gestión de Mesas
- Crear, editar y eliminar mesas
- Mapa visual con estado en tiempo real
- Cambio rápido de estados
- Asignación automática a comandas

### 2. Sistema de Comandas
- Crear pedidos por mesa
- Agregar/quitar productos
- Seguimiento de estado
- Observaciones especiales
- Histórico de pedidos

### 3. Caja y Pagos
- Apertura y cierre de turnos
- Múltiples métodos de pago
- Cálculo automático de cambio
- Generación de tickets
- Control de diferencias

### 4. Inventario
- Gestión de productos y categorías
- Control de stock
- Alertas de reabastecimiento
- Ajuste de inventario
- Precios y disponibilidad

### 5. Reportes y Estadísticas
- Ventas por período
- Productos más vendidos
- Desempeño de meseros
- Ocupación de mesas
- Reporte de turnos
- Dashboard ejecutivo

## 🛠️ Comandos Útiles

### Ver logs de la aplicación
```bash
docker-compose logs -f web
```

### Reiniciar la base de datos
```bash
docker-compose down -v
docker-compose up --build
```

### Acceder al contenedor de la aplicación
```bash
docker-compose exec web bash
```

### Crear backup de la base de datos
```bash
docker-compose exec db pg_dump -U restaurant restaurant_db > backup.sql
```

### Restaurar backup
```bash
docker-compose exec -T db psql -U restaurant restaurant_db < backup.sql
```

## 🔧 Configuración Avanzada

### Variables de Entorno

Editar `docker-compose.yml` para cambiar:

```yaml
environment:
  - FLASK_ENV=production          # development o production
  - SECRET_KEY=tu-clave-secreta   # Cambiar en producción
  - DATABASE_URL=...              # URL de base de datos
```

### Modificar Puerto

En `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Cambiar 8080 por el puerto deseado
```

## 🐛 Solución de Problemas

### La aplicación no inicia
```bash
# Verificar logs
docker-compose logs web

# Reiniciar servicios
docker-compose restart
```

### Error de conexión a base de datos
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Recrear contenedores
docker-compose down
docker-compose up --build
```

### Resetear base de datos
```bash
# Detener servicios y eliminar volúmenes
docker-compose down -v

# Reiniciar
docker-compose up --build
```

## 📝 Próximas Mejoras

- [ ] Reservaciones de mesas
- [ ] Integración con impresoras térmicas
- [ ] App móvil para meseros
- [ ] Sistema de propinas
- [ ] Programa de lealtad
- [ ] Integración con delivery
- [ ] Multi-sucursal
- [ ] Reportes avanzados con gráficos
- [ ] Exportación a Excel/PDF
- [ ] API REST completa

## 🤝 Soporte

Para reportar problemas o sugerencias, contactar al administrador del sistema.

## 📄 Licencia

Sistema propietario para uso interno.

---

**Versión:** 1.0.0  
**Fecha:** Octubre 2025