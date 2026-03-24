"""
docker_manager.py - Gestión de contenedores Docker
Usa el Docker SDK para Python para construir imágenes, crear y eliminar contenedores.
"""

import ast
import os
import re
import shutil
import tempfile
import time

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
    
    
    def validate_code(self, language, code):
        """
        Valida la sintaxis del código del usuario antes de construir la imagen.
        Lanza ValueError si el código tiene errores de sintaxis.
        """
        if language == "python":
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                raise ValueError(f"Error de sintaxis en Python (línea {e.lineno}): {e.msg}")

            # Verificar que define la función process
            defines_process = any(
                isinstance(node, ast.FunctionDef) and node.name == "process"
                for node in ast.walk(tree)
            )
            if not defines_process:
                raise ValueError("El código debe definir una función 'process(data)'")

            # Solo se permite un docstring opcional y la función process(data) en el nivel superior.
            for node in tree.body:
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    continue

                if isinstance(node, ast.FunctionDef) and node.name == "process":
                    continue

                raise ValueError(
                    f"Línea {node.lineno}: no se permite código fuera de 'process(data)'. "
                    "Mueve variables, imports y lógica auxiliar dentro de esa función."
                )

        elif language == "node":
            if "module.exports" not in code:
                raise ValueError(
                    "El código Node.js debe exportar la función principal con "
                    "'module.exports = process'"
                )

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

    def list_managed_services(self, all_containers=False):
        """
        Lista los microservicios administrados por la plataforma.
        Por defecto retorna solo los que están corriendo.
        """
        containers = self.client.containers.list(
            all=all_containers,
            filters={"label": "platform=microservices-un"}
        )

        services = []
        for container in containers:
            labels = container.labels
            service_name = labels.get("service_name")
            service_port = labels.get("service_port")

            if not service_name or not service_port:
                continue

            services.append({
                "name": service_name,
                "port": int(service_port),
                "language": labels.get("service_language"),
                "status": container.status,
                "container_name": container.name
            })

        return services

    def _format_startup_error(self, logs):
        """
        Intenta resumir errores comunes de arranque para mostrarlos de forma amigable.
        """
        node_match = re.search(
            r"/app/user_code\.js:(\d+).*?SyntaxError:\s*(.+)",
            logs,
            re.DOTALL
        )
        if node_match:
            line = node_match.group(1)
            message = node_match.group(2).splitlines()[0].strip()
            return f"Error de sintaxis en Node.js (línea {line}): {message}"

        python_match = re.search(
            r'File "/app/user_code\.py", line (\d+).*?SyntaxError:\s*(.+)',
            logs,
            re.DOTALL
        )
        if python_match:
            line = python_match.group(1)
            message = python_match.group(2).splitlines()[0].strip()
            return f"Error de sintaxis en Python (línea {line}): {message}"

        return None

    def _wait_for_container_startup(self, container, timeout=10, stable_seconds=2):
        """
        Espera a que el contenedor quede estable o falle durante el arranque.
        """
        deadline = time.time() + timeout

        while time.time() < deadline:
            container.reload()

            if container.status == "running":
                time.sleep(stable_seconds)
                container.reload()
                if container.status == "running":
                    return

            if container.status in {"exited", "dead"}:
                logs = container.logs(tail=50).decode("utf-8", errors="replace").strip()
                friendly_error = self._format_startup_error(logs)
                if friendly_error:
                    raise Exception(friendly_error)
                raise Exception(
                    "El contenedor del microservicio no inició correctamente.\n"
                    f"Estado: {container.status}\n"
                    f"Logs:\n{logs or '(sin logs)'}"
                )

            time.sleep(0.5)

        container.reload()
        if container.status != "running":
            raise Exception(
                "El contenedor del microservicio no alcanzó el estado 'running' "
                f"dentro de {timeout} segundos. Estado actual: {container.status}"
            )

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
        # Validar sintaxis del código antes de construir la imagen
        self.validate_code(language, code)
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
                network=self.network_name
            )

            self._wait_for_container_startup(container)
            container.update(restart_policy={"Name": "unless-stopped"})
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
