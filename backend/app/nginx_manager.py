"""
nginx_manager.py - Gestión dinámica de configuración de Nginx
Genera archivos de configuración y recarga Nginx cuando se crean/eliminan microservicios.
"""

import os
import subprocess
from app.config import Config


class NginxManager:
    """Genera configuraciones dinámicas de Nginx para cada microservicio."""

    def __init__(self):
        self.dynamic_dir = Config.NGINX_DYNAMIC_DIR
        self.nginx_container = Config.NGINX_CONTAINER_NAME
        os.makedirs(self.dynamic_dir, exist_ok=True)

    def add_service(self, name, port):
        """
        Genera un archivo de configuración de Nginx para un microservicio.
        Crea: /etc/nginx/dynamic/{name}.conf
        """
        config_content = f"""# Configuración dinámica para microservicio: {name}
location /services/{name} {{
    rewrite ^/services/{name}(.*) /$1 break;
    proxy_pass http://ms-{name}:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 30s;
    proxy_connect_timeout 10s;
}}
"""
        config_path = os.path.join(self.dynamic_dir, f"{name}.conf")
        with open(config_path, "w") as f:
            f.write(config_content)

    def remove_service(self, name):
        """Elimina el archivo de configuración de Nginx para un microservicio."""
        config_path = os.path.join(self.dynamic_dir, f"{name}.conf")
        if os.path.exists(config_path):
            os.remove(config_path)

    def reload(self):
        """
        Recarga la configuración de Nginx sin reiniciar el contenedor.
        Usa docker exec para enviar la señal de reload.
        """
        try:
            import docker
            client = docker.from_env()
            nginx = client.containers.get(self.nginx_container)
            nginx.exec_run("nginx -s reload")
        except Exception as e:
            print(f"[WARN] No se pudo recargar Nginx: {e}")
