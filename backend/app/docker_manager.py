"""
docker_manager.py - Gestión de contenedores Docker
Usa el Docker SDK para Python para construir imágenes, crear y eliminar contenedores.
"""

import os
import tempfile
import shutil
import docker
from app.config import Config


class DockerManager:
    """Gestiona el ciclo de vida de contenedores Docker para microservicios."""

    def __init__(self):
        self.client = docker.from_env()
        self.network_name = Config.DOCKER_NETWORK
        self.base_port = Config.BASE_PORT
        self._ensure_network()

    def _ensure_network(self):
        """Asegura que la red Docker personalizada exista."""
        try:
            self.client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.client.networks.create(self.network_name, driver="bridge")

    def check_connection(self):
        """Verifica la conexión con Docker daemon."""
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def _get_next_port(self):
        """Asigna el siguiente puerto disponible para un microservicio."""
        containers = self.client.containers.list(
            all=True,
            filters={"label": "platform=microservices-un"}
        )
        used_ports = set()
        for container in containers:
            labels = container.labels
            if "service_port" in labels:
                used_ports.add(int(labels["service_port"]))

        port = self.base_port
        while port in used_ports:
            port += 1
        return port

    def _build_context(self, name, language, code):
        """
        Genera el contexto de build (Dockerfile + código) en un directorio temporal.
        Retorna la ruta al directorio temporal.
        """
        build_dir = tempfile.mkdtemp(prefix=f"ms-{name}-")
        templates_dir = Config.TEMPLATES_DIR

        if language == "python":
            # Copiar Dockerfile template
            dockerfile_template = os.path.join(templates_dir, "python", "Dockerfile.template")
            with open(dockerfile_template, "r") as f:
                dockerfile_content = f.read()

            # Copiar wrapper template
            wrapper_template = os.path.join(templates_dir, "python", "wrapper.py.template")
            with open(wrapper_template, "r") as f:
                wrapper_content = f.read()

            # Escribir el código del usuario
            with open(os.path.join(build_dir, "user_code.py"), "w") as f:
                f.write(code)

            # Escribir el wrapper
            with open(os.path.join(build_dir, "server.py"), "w") as f:
                f.write(wrapper_content)

            # Escribir Dockerfile
            with open(os.path.join(build_dir, "Dockerfile"), "w") as f:
                f.write(dockerfile_content)

        elif language == "node":
            # Copiar Dockerfile template
            dockerfile_template = os.path.join(templates_dir, "node", "Dockerfile.template")
            with open(dockerfile_template, "r") as f:
                dockerfile_content = f.read()

            # Copiar wrapper template
            wrapper_template = os.path.join(templates_dir, "node", "wrapper.js.template")
            with open(wrapper_template, "r") as f:
                wrapper_content = f.read()

            # Escribir el código del usuario
            with open(os.path.join(build_dir, "user_code.js"), "w") as f:
                f.write(code)

            # Escribir el wrapper
            with open(os.path.join(build_dir, "server.js"), "w") as f:
                f.write(wrapper_content)

            # Escribir Dockerfile
            with open(os.path.join(build_dir, "Dockerfile"), "w") as f:
                f.write(dockerfile_content)

            # Crear package.json básico
            package_json = '{"name":"microservice","version":"1.0.0","dependencies":{"express":"^4.18.0"}}'
            with open(os.path.join(build_dir, "package.json"), "w") as f:
                f.write(package_json)

        return build_dir

    def create_service(self, name, language, code):
        """
        Construye la imagen Docker y levanta el contenedor para un microservicio.
        Retorna el puerto asignado.
        """
        port = self._get_next_port()
        image_name = f"ms-{name}:latest"
        container_name = f"ms-{name}"

        # Generar contexto de build
        build_dir = self._build_context(name, language, code)

        try:
            # Construir imagen
            self.client.images.build(
                path=build_dir,
                tag=image_name,
                rm=True
            )

            # Crear y ejecutar contenedor
            container = self.client.containers.run(
                image=image_name,
                name=container_name,
                detach=True,
                ports={"8080/tcp": port},
                labels={
                    "platform": "microservices-un",
                    "service_name": name,
                    "service_port": str(port),
                    "service_language": language
                },
                network=self.network_name,
                restart_policy={"Name": "unless-stopped"}
            )

            return port

        finally:
            # Limpiar directorio temporal
            shutil.rmtree(build_dir, ignore_errors=True)

    def start_service(self, name):
        """Inicia un contenedor detenido."""
        container_name = f"ms-{name}"
        try:
            container = self.client.containers.get(container_name)
            container.start()
        except docker.errors.NotFound:
            raise Exception(f"Contenedor '{container_name}' no encontrado")

    def stop_service(self, name):
        """Detiene un contenedor sin eliminarlo."""
        container_name = f"ms-{name}"
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=10)
        except docker.errors.NotFound:
            raise Exception(f"Contenedor '{container_name}' no encontrado")

    def remove_service(self, name):
        """Elimina el contenedor y la imagen de un microservicio."""
        container_name = f"ms-{name}"
        image_name = f"ms-{name}:latest"

        # Eliminar contenedor
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=10)
            container.remove(force=True)
        except docker.errors.NotFound:
            pass

        # Eliminar imagen
        try:
            self.client.images.remove(image_name, force=True)
        except docker.errors.ImageNotFound:
            pass

    def get_service_status(self, name):
        """Obtiene el estado actual de un contenedor."""
        container_name = f"ms-{name}"
        try:
            container = self.client.containers.get(container_name)
            return container.status  # running, exited, paused, etc.
        except docker.errors.NotFound:
            return "not_found"
