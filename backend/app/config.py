"""
config.py - Configuración de la aplicación backend.
"""

import os


class Config:
    """Configuración central del backend."""

    # Flask
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    SECRET_KEY = os.environ.get("SECRET_KEY", "microservices-platform-secret")

    # Docker
    DOCKER_NETWORK = os.environ.get("DOCKER_NETWORK", "microservices-net")
    BASE_PORT = int(os.environ.get("BASE_PORT", "9001"))

    # Nginx
    NGINX_DYNAMIC_DIR = os.environ.get("NGINX_DYNAMIC_DIR", "/etc/nginx/dynamic")
    NGINX_CONTAINER_NAME = os.environ.get("NGINX_CONTAINER_NAME", "nginx-proxy")

    # Templates
    TEMPLATES_DIR = os.environ.get("TEMPLATES_DIR", "/app/templates")
