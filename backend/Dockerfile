FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para Docker SDK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app/ ./app/

# Los templates se montan como volumen en docker-compose.yml

# Exponer puerto
EXPOSE 5000

# Comando de inicio
CMD ["python", "-m", "flask", "--app", "app.main", "run", "--host", "0.0.0.0", "--port", "5000"]
