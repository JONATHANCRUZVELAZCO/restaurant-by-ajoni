Despliegue en Render + Neon (Postgres)
=====================================

Este documento resume los pasos para ver la aplicación en producción usando Render (Web Service con Docker) y Neon (Postgres).

Pasos resumidos
---------------

1. Subir el repo a GitHub (o conectar el repo existente) y verificar que el `Dockerfile` está en la raíz.
2. Crear una base de datos en Neon y copiar la URL de conexión (DATABASE_URL, formato: `postgresql://...`).
3. En Render crea un nuevo Web Service y conecta el repo. Selecciona `Docker` como entorno.
   - Opcional: usa `render.yaml` en la raíz para manejar la configuración.
4. En el dashboard de Render, en Settings -> Environment, añadir variables de entorno:
   - `DATABASE_URL` = (la URL que Neon te da)
   - `SECRET_KEY` = (una cadena larga aleatoria)
   - `FLASK_ENV` = `production`
5. Desplegar. Revisar los logs desde el panel de Deploys / Logs.

Migraciones (Flask-Migrate)
---------------------------

1. En local (o en Render shell) inicializa migraciones:

   - Instalar dependencias: `pip install -r requirements.txt`
   - Inicializar: `flask db init` (solo la primera vez)
   - Crear migración: `flask db migrate -m "Initial"`
   - Aplicar migración: `flask db upgrade`

2. En Render puedes correr estas mismas órdenes abriendo una shell (`Shell` en el web service) o creando un job temporal que ejecute `flask db upgrade` después del despliegue.

Neon specifics
--------------

- Neon provee una URL de conexión. Usa esa URL directamente en `DATABASE_URL`.
- Si Neon te da un pooler o branch, usa la URL del branch que tenga el pooler (mejor para conexiones desde servicios como Render).

Probar la API desde Android
---------------------------

- Exponer endpoints REST/JSON. Asegúrate de que tus rutas API retornan JSON y que tienes CORS habilitado si tu app Android usa peticiones desde un webview o similar.
- Usa Postman o curl para verificar `https://<service>.onrender.com/api/` antes de integrar en Android.

Notas finales
------------

- Este README asume que tu aplicación usa `SQLAlchemy` y `Flask-Migrate` para migraciones.
- Ajusta `render.yaml` y variables de entorno según necesites.
