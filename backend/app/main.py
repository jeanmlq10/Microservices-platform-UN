"""
main.py - Aplicación principal Flask
API REST para gestionar el ciclo de vida de microservicios dinámicos.
"""

import os
import re
import unicodedata
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
store = ServiceStore(Config.SERVICES_STORE_PATH)


def reconcile_service_store():
    """
    Rehidrata el store persistido usando su metadata guardada y el estado real de Docker.
    """
    try:
        persisted_services = {
            service["name"]: service
            for service in store.get_all()
        }
        managed_services = docker_mgr.list_managed_services(all_containers=True)
        hydrated_services = []

        for service in managed_services:
            persisted = persisted_services.get(service["name"], {})
            hydrated_services.append({
                "name": service["name"],
                "description": persisted.get("description", ""),
                "language": persisted.get("language") or service["language"] or "unknown",
                "port": service["port"],
                "status": service["status"],
                "endpoint": f"/services/{service['name']}",
                "code": persisted.get("code", ""),
                "created_at": persisted.get("created_at", "")
            })

        store.load_services(hydrated_services)
        print(f"[INFO] Store de servicios rehidratado: {len(hydrated_services)} servicio(s) encontrados")
    except Exception as e:
        print(f"[WARN] No se pudo rehidratar el store de servicios: {e}")


def reconcile_nginx_dynamic_config():
    """
    Sincroniza las configuraciones dinámicas con el estado real de Docker.
    Evita que Nginx cargue upstreams huérfanos persistidos en el volumen.
    """
    try:
        running_services = docker_mgr.list_managed_services()
        nginx_mgr.sync_services(running_services)
        nginx_mgr.reload()
        print(f"[INFO] Configuración dinámica de Nginx reconciliada: {len(running_services)} servicio(s) activos")
    except Exception as e:
        print(f"[WARN] No se pudo reconciliar la configuración dinámica de Nginx: {e}")


reconcile_service_store()
reconcile_nginx_dynamic_config()


def normalize_service_name(raw_name):
    """Convierte el nombre ingresado por el usuario en un slug seguro para Docker."""
    normalized = unicodedata.normalize("NFKD", raw_name.strip().lower())
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug


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
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Body JSON invalido o vacio"}), 400

    # Validaciones
    required_fields = ["name", "language", "code"]
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({"error": f"Campo '{field}' es requerido"}), 400

    original_name = data["name"].strip()
    name = normalize_service_name(original_name)
    language = data["language"].strip().lower()
    code = data["code"]
    description = data.get("description", "").strip()

    if not name:
        return jsonify({"error": "El nombre del microservicio no es valido"}), 400

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
        cleanup_errors = []
        try:
            docker_mgr.remove_service(name)
        except Exception as cleanup_error:
            cleanup_errors.append(f"Docker cleanup: {cleanup_error}")

        try:
            nginx_mgr.remove_service(name)
        except Exception as cleanup_error:
            cleanup_errors.append(f"Nginx cleanup: {cleanup_error}")

        error_message = f"Error al crear microservicio: {str(e)}"
        if cleanup_errors:
            error_message += "\n" + "\n".join(cleanup_errors)

        return jsonify({"error": error_message}), 500


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
