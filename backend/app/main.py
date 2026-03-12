"""
main.py - Aplicación principal Flask
API REST para gestionar el ciclo de vida de microservicios dinámicos.
"""

import os
from flask import Flask, request, jsonify
from app.docker_manager import DockerManager
from app.nginx_manager import NginxManager
from app.models import ServiceStore
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar managers
docker_mgr = DockerManager()
nginx_mgr = NginxManager()
store = ServiceStore()


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check del backend y conexión con Docker."""
    docker_status = docker_mgr.check_connection()
    return jsonify({
        "status": "healthy",
        "docker": "connected" if docker_status else "disconnected",
        "services_count": store.count()
    })


@app.route("/api/services", methods=["GET"])
def list_services():
    """Listar todos los microservicios registrados."""
    services = store.get_all()
    return jsonify({
        "services": services,
        "total": len(services)
    })


@app.route("/api/services", methods=["POST"])
def create_service():
    """
    Crear un nuevo microservicio.
    Body JSON esperado:
    {
        "name": "nombre-del-servicio",
        "description": "Descripción del servicio",
        "language": "python" | "node",
        "code": "código fuente del microservicio"
    }
    """
    data = request.get_json()

    # Validaciones
    required_fields = ["name", "language", "code"]
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({"error": f"Campo '{field}' es requerido"}), 400

    name = data["name"].strip().lower().replace(" ", "-")
    language = data["language"].strip().lower()
    code = data["code"]
    description = data.get("description", "").strip()

    # Validar lenguaje soportado
    if language not in ["python", "node"]:
        return jsonify({"error": "Lenguaje no soportado. Use 'python' o 'node'"}), 400

    # Validar nombre único
    if store.exists(name):
        return jsonify({"error": f"Ya existe un microservicio con el nombre '{name}'"}), 409

    try:
        # Construir imagen y levantar contenedor
        port = docker_mgr.create_service(name, language, code)

        # Actualizar configuración de Nginx
        nginx_mgr.add_service(name, port)
        nginx_mgr.reload()

        # Registrar en el store
        service_info = store.add(
            name=name,
            description=description,
            language=language,
            port=port,
            code=code
        )

        return jsonify(service_info), 201

    except Exception as e:
        # Limpiar en caso de error
        docker_mgr.remove_service(name)
        nginx_mgr.remove_service(name)
        return jsonify({"error": f"Error al crear microservicio: {str(e)}"}), 500


@app.route("/api/services/<name>", methods=["GET"])
def get_service(name):
    """Obtener detalles de un microservicio específico."""
    service = store.get(name)
    if not service:
        return jsonify({"error": f"Microservicio '{name}' no encontrado"}), 404
    return jsonify(service)


@app.route("/api/services/<name>/enable", methods=["PUT"])
def enable_service(name):
    """Habilitar (iniciar) un microservicio deshabilitado."""
    service = store.get(name)
    if not service:
        return jsonify({"error": f"Microservicio '{name}' no encontrado"}), 404

    try:
        docker_mgr.start_service(name)
        nginx_mgr.add_service(name, service["port"])
        nginx_mgr.reload()
        store.update_status(name, "running")
        return jsonify({"message": f"Microservicio '{name}' habilitado", "status": "running"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/services/<name>/disable", methods=["PUT"])
def disable_service(name):
    """Deshabilitar (detener) un microservicio sin eliminarlo."""
    service = store.get(name)
    if not service:
        return jsonify({"error": f"Microservicio '{name}' no encontrado"}), 404

    try:
        docker_mgr.stop_service(name)
        nginx_mgr.remove_service(name)
        nginx_mgr.reload()
        store.update_status(name, "stopped")
        return jsonify({"message": f"Microservicio '{name}' deshabilitado", "status": "stopped"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/services/<name>", methods=["DELETE"])
def delete_service(name):
    """Eliminar completamente un microservicio (contenedor + imagen)."""
    service = store.get(name)
    if not service:
        return jsonify({"error": f"Microservicio '{name}' no encontrado"}), 404

    try:
        docker_mgr.remove_service(name)
        nginx_mgr.remove_service(name)
        nginx_mgr.reload()
        store.remove(name)
        return jsonify({"message": f"Microservicio '{name}' eliminado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
