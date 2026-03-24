"""
models.py - Almacén de datos de microservicios
Almacena la información de los microservicios en memoria y la persiste en disco.
"""

import json
import os
from datetime import datetime, timezone


class ServiceStore:
    """Almacén persistente para los microservicios registrados."""

    def __init__(self, storage_path):
        self.storage_path = storage_path
        self._services = {}
        self._ensure_storage_dir()
        self._load_from_disk()

    def _ensure_storage_dir(self):
        """Asegura que exista el directorio de persistencia."""
        storage_dir = os.path.dirname(self.storage_path)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)

    def _load_from_disk(self):
        """Carga el store desde disco si existe."""
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                services = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        if isinstance(services, list):
            self._services = {
                service["name"]: service
                for service in services
                if isinstance(service, dict) and "name" in service
            }

    def _save_to_disk(self):
        """Guarda el store actual en disco."""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.get_all(), f, ensure_ascii=True, indent=2)

    def add(self, name, description, language, port, code):
        """Registra un nuevo microservicio."""
        service = {
            "name": name,
            "description": description,
            "language": language,
            "port": port,
            "status": "running",
            "endpoint": f"/services/{name}",
            "code": code,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._services[name] = service
        self._save_to_disk()
        return service

    def load_services(self, services):
        """Reemplaza el almacén actual con una lista de servicios."""
        self._services = {service["name"]: service for service in services}
        self._save_to_disk()

    def get(self, name):
        """Obtiene la información de un microservicio por nombre."""
        return self._services.get(name)

    def get_all(self):
        """Retorna la lista de todos los microservicios."""
        return list(self._services.values())

    def exists(self, name):
        """Verifica si un microservicio con ese nombre ya existe."""
        return name in self._services

    def update_status(self, name, status):
        """Actualiza el estado de un microservicio."""
        if name in self._services:
            self._services[name]["status"] = status
            self._save_to_disk()

    def remove(self, name):
        """Elimina un microservicio del registro."""
        if name in self._services:
            del self._services[name]
            self._save_to_disk()

    def count(self):
        """Retorna la cantidad de microservicios registrados."""
        return len(self._services)
