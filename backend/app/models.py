"""
models.py - Almacén de datos de microservicios
Almacena la información de los microservicios creados en memoria.
"""

from datetime import datetime, timezone


class ServiceStore:
    """Almacén en memoria para los microservicios registrados."""

    def __init__(self):
        self._services = {}

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
        return service

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

    def remove(self, name):
        """Elimina un microservicio del registro."""
        if name in self._services:
            del self._services[name]

    def count(self):
        """Retorna la cantidad de microservicios registrados."""
        return len(self._services)
