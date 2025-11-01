FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 5000

# Variables de entorno
ENV FLASK_APP=run.py
ENV PYTHONUNBUFFERED=1

# Comando de inicio: usar la variable PORT si está disponible (Render la provee)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --timeout 120 run:app"]