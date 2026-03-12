# 🚀 Plataforma de Microservicios Dinámicos - UN

> Plataforma basada en microservicios que permite crear, administrar y eliminar microservicios de forma dinámica a través de un dashboard web. Cada microservicio se ejecuta en su propio contenedor Docker y se expone automáticamente como endpoint HTTP.

---

## 📋 Tabla de Contenidos

- [Equipo de Trabajo](#-equipo-de-trabajo)
- [Descripción del Proyecto](#-descripción-del-proyecto)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Stack Tecnológico](#-stack-tecnológico)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Distribución del Trabajo](#-distribución-del-trabajo)
- [Estrategia de Ramas Git](#-estrategia-de-ramas-git)
- [Cronograma de Trabajo](#-cronograma-de-trabajo)
- [Instalación y Ejecución](#-instalación-y-ejecución)
- [Uso del Dashboard](#-uso-del-dashboard)
- [Ejemplos Funcionales](#-ejemplos-funcionales)
- [API Reference](#-api-reference)
- [Video de Demostración](#-video-de-demostración)

---

## 👥 Equipo de Trabajo

| Integrante | Rol | Rama de Trabajo |
|------------|-----|-----------------|
| **Jean Marthé** | 🔧 Infraestructura & Proxy | `feature/infrastructure` |
| **Valentina Schotborgh** | ⚙️ Backend / Motor de Microservicios | `feature/backend-api` |
| **Oscar Gil** | 🎨 Frontend / Dashboard | `feature/frontend` |
| **Alberto Niebles** | 🧪 Templates, Testing & Documentación | `feature/templates-docs` |

---

## 📖 Descripción del Proyecto

### ¿Qué hace esta plataforma?

Esta plataforma permite a los usuarios **crear microservicios en tiempo real** desde un navegador web. El flujo es simple:

1. El usuario abre el **dashboard web**.
2. **Pega el código fuente** de su microservicio (Python o Node.js).
3. Selecciona el **lenguaje de programación**.
4. Le asigna un **nombre** y una **descripción**.
5. La plataforma **construye automáticamente** una imagen Docker, **levanta un contenedor** y **expone el microservicio** como un endpoint HTTP accesible.

### ¿Qué es un microservicio en este proyecto?

✅ **SÍ es un microservicio:**
- Una aplicación independiente
- Empaquetada y ejecutada en su propio contenedor Docker
- Que expone al menos un endpoint HTTP
- Que recibe parámetros de entrada y retorna una respuesta en formato JSON
- Que **no existe previamente** y se crea dinámicamente desde la plataforma

❌ **NO es un microservicio:**
- Una función interna del dashboard
- Un archivo suelto
- Una ruta adicional del backend principal

---

## 🏗️ Arquitectura del Sistema

### Diagrama General

```
                        ┌──────────────────┐
                        │   USUARIO        │
                        │   (Browser)      │
                        └────────┬─────────┘
                                 │ Puerto :80
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│                     NGINX (Reverse Proxy)                       │
│                        Puerto :80                               │
│                                                                 │
│  Ruta /             →  Frontend (Dashboard)       [:3000]       │
│  Ruta /api/*        →  Backend (API Flask)        [:5000]       │
│  Ruta /services/*   →  Microservicios Dinámicos   [:DINÁMICO]   │
│                                                                 │
│  ⚡ La config se regenera dinámicamente con cada nuevo servicio │
└────┬──────────────────┬────────────────────┬───────────────────┘
     │                  │                    │
     ▼                  ▼                    ▼
┌──────────┐    ┌──────────────┐    ┌─────────────────────┐
│ FRONTEND │    │   BACKEND    │    │  MICROSERVICIO N    │
│          │    │              │    │  (Contenedor        │
│ HTML/CSS │    │ Python Flask │    │   Dinámico)         │
│ Vanilla  │    │ Docker SDK   │    │                     │
│ JS       │    │              │    │  Puerto asignado    │
│          │    │ Puerto :5000 │    │  automáticamente    │
│ Puerto   │    │              │    │                     │
│ :3000    │    └──────┬───────┘    └─────────────────────┘
└──────────┘           │
                       │ Monta /var/run/docker.sock
                       ▼
              ┌─────────────────┐
              │  Docker Engine  │
              │                 │
              │ • Construye     │
              │   imágenes      │
              │ • Crea/elimina  │
              │   contenedores  │
              │ • Gestiona red  │
              └─────────────────┘
```

### Flujo Detallado de Creación de un Microservicio

```
  USUARIO                NGINX              BACKEND               DOCKER ENGINE
    │                      │                   │                       │
    │  1. Pega código      │                   │                       │
    │     en dashboard     │                   │                       │
    │ ──────────────────►  │                   │                       │
    │                      │  2. POST /api/    │                       │
    │                      │     services      │                       │
    │                      │ ────────────────► │                       │
    │                      │                   │  3. Genera Dockerfile │
    │                      │                   │     dinámicamente     │
    │                      │                   │ ────────────────────► │
    │                      │                   │                       │
    │                      │                   │  4. docker build      │
    │                      │                   │ ────────────────────► │
    │                      │                   │                       │
    │                      │                   │  5. docker run        │
    │                      │                   │     (puerto dinámico) │
    │                      │                   │ ────────────────────► │
    │                      │                   │                       │
    │                      │                   │  6. Actualiza config  │
    │                      │  7. Recarga Nginx │     de Nginx          │
    │                      │ ◄──────────────── │                       │
    │                      │                   │                       │
    │  8. Microservicio    │                   │                       │
    │     disponible en    │                   │                       │
    │     /services/{name} │                   │                       │
    │ ◄──────────────────  │                   │                       │
```

### Componentes del Sistema

| Componente | Descripción | Puerto |
|------------|-------------|--------|
| **Nginx** | Reverse proxy principal. Punto de entrada único. Enruta tráfico al frontend, backend y microservicios dinámicos. | `:80` |
| **Frontend** | Dashboard web para crear, listar, habilitar/deshabilitar y eliminar microservicios. | `:3000` |
| **Backend** | API REST que gestiona el ciclo de vida de los microservicios. Usa Docker SDK para construir imágenes y crear contenedores. | `:5000` |
| **Microservicios** | Contenedores creados dinámicamente por el usuario. Cada uno corre en su propio puerto asignado automáticamente. | `:9001+` |

### Red Docker

Todos los contenedores están conectados a una **red Docker bridge personalizada** llamada `microservices-net`, lo que permite:
- Comunicación por nombre de contenedor (DNS interno de Docker)
- Aislamiento de la red del host
- Resolución dinámica de microservicios por Nginx

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Justificación |
|------------|------------|---------------|
| **Reverse Proxy** | Nginx | Servidor principal, enruta dinámicamente a los microservicios |
| **Backend API** | Python 3.12 + Flask | Docker SDK para Python es maduro y fácil de usar |
| **Frontend** | HTML5 + CSS3 + JavaScript (Vanilla) | Sin dependencias de build, simple y ligero |
| **Contenedores** | Docker + Docker Compose | Requisito del proyecto, todo sube con un solo comando |
| **Lenguajes soportados** | Python 🐍 + Node.js 🟢 | Mínimo 2 lenguajes como requiere el enunciado |
| **Docker SDK** | `docker` (pip) | Permite crear/eliminar contenedores programáticamente |

### ¿Por qué Docker Socket en lugar de Docker-in-Docker?

El backend **monta el Docker socket** (`/var/run/docker.sock`) como volumen. Esto es más eficiente que Docker-in-Docker (DinD) porque:

- ✅ No necesita un daemon Docker adicional dentro del contenedor
- ✅ Las imágenes se comparten con el host (sin duplicación)
- ✅ Menor consumo de recursos
- ✅ Más rápido en la construcción de imágenes

---

## 📁 Estructura del Proyecto

```
Microservices-platform-UN/
│
├── 📄 docker-compose.yml               # Orquestación - levanta todo con un solo comando
├── 📄 .env                              # Variables de entorno (puertos, nombres de red, etc.)
├── 📄 README.md                         # Este archivo
├── 📄 .gitignore                        # Archivos ignorados por Git
│
├── 📂 nginx/                            # ═══ PERSONA 1: Jean Marthé ═══
│   ├── 📄 Dockerfile                    # Imagen personalizada de Nginx
│   ├── 📄 nginx.conf                    # Configuración principal de Nginx
│   ├── 📄 default.conf                  # Server block principal con rutas base
│   └── 📂 dynamic/                      # Configs generadas dinámicamente
│       └── 📄 .gitkeep                  # (se generan en runtime para cada microservicio)
│
├── 📂 backend/                          # ═══ PERSONA 2: Valentina Schotborgh ═══
│   ├── 📄 Dockerfile                    # Imagen del backend
│   ├── 📄 requirements.txt             # Dependencias Python
│   └── 📂 app/
│       ├── 📄 __init__.py
│       ├── 📄 main.py                  # App Flask - rutas principales de la API
│       ├── 📄 docker_manager.py        # Lógica para crear/eliminar contenedores Docker
│       ├── 📄 nginx_manager.py         # Genera y recarga configs de Nginx
│       ├── 📄 models.py                # Modelos de datos (info de microservicios)
│       └── 📄 config.py                # Configuración de la aplicación
│
├── 📂 frontend/                         # ═══ PERSONA 3: Oscar Gil ═══
│   ├── 📄 Dockerfile                    # Imagen del frontend (Nginx sirve estáticos)
│   └── 📂 src/
│       ├── 📄 index.html               # Página principal del dashboard
│       ├── 📄 app.js                   # Lógica del dashboard (fetch API, DOM)
│       └── 📄 styles.css               # Estilos del dashboard
│
└── 📂 templates/                        # ═══ PERSONA 4: Alberto Niebles ═══
    ├── 📂 python/
    │   ├── 📄 Dockerfile.template      # Template Dockerfile para microservicios Python
    │   └── 📄 wrapper.py.template      # Wrapper Flask para el código del usuario
    ├── 📂 node/
    │   ├── 📄 Dockerfile.template      # Template Dockerfile para microservicios Node.js
    │   └── 📄 wrapper.js.template      # Wrapper Express para el código del usuario
    └── 📂 examples/
        ├── 📄 python_hello.py          # Ejemplo: Hola Mundo en Python
        ├── 📄 python_sum.py            # Ejemplo: Suma de dos valores en Python
        ├── 📄 node_hello.js            # Ejemplo: Hola Mundo en Node.js
        └── 📄 node_sum.js              # Ejemplo: Suma de dos valores en Node.js
```

---

## 👷 Distribución del Trabajo

### 🔧 Persona 1: Jean Marthé — Infraestructura & Proxy

**Rama:** `feature/infrastructure`

**Responsabilidades:**
- [ ] Configurar `docker-compose.yml` con todos los servicios base (nginx, backend, frontend)
- [ ] Definir la red Docker personalizada `microservices-net`
- [ ] Configurar Nginx como reverse proxy con las rutas:
  - `/` → Frontend
  - `/api/*` → Backend
  - `/services/*` → Microservicios dinámicos
- [ ] Implementar el mecanismo de recarga dinámica de Nginx (cuando se crea/elimina un microservicio)
- [ ] Configurar volúmenes compartidos entre backend y Nginx para configs dinámicas
- [ ] Crear el `Dockerfile` de Nginx
- [ ] Archivo `.env` con variables de entorno del proyecto
- [ ] Asegurar que `docker-compose up` levante todo correctamente

**Archivos principales:**
```
docker-compose.yml
.env
nginx/Dockerfile
nginx/nginx.conf
nginx/default.conf
nginx/dynamic/.gitkeep
```

**Conocimientos clave:**
- Docker Compose (networks, volumes, depends_on)
- Nginx (proxy_pass, upstream, include, reload)
- Docker networking

---

### ⚙️ Persona 2: Valentina Schotborgh — Backend / Motor de Microservicios

**Rama:** `feature/backend-api`

**Responsabilidades:**
- [ ] API REST con Flask para el CRUD de microservicios
- [ ] Integración con Docker SDK (`docker` Python package) para:
  - Construir imágenes Docker dinámicamente
  - Crear y ejecutar contenedores
  - Detener y eliminar contenedores
  - Listar contenedores activos
- [ ] Generación dinámica de Dockerfiles usando los templates
- [ ] Asignación automática de puertos
- [ ] Gestión de estado de microservicios (habilitado/deshabilitado)
- [ ] Comunicación con Nginx para actualizar la configuración al crear/eliminar servicios
- [ ] Manejo de errores y validaciones
- [ ] Dockerfile del backend

**Archivos principales:**
```
backend/Dockerfile
backend/requirements.txt
backend/app/__init__.py
backend/app/main.py
backend/app/docker_manager.py
backend/app/nginx_manager.py
backend/app/models.py
backend/app/config.py
```

**Endpoints de la API:**

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/services` | Crear un nuevo microservicio |
| `GET` | `/api/services` | Listar todos los microservicios |
| `GET` | `/api/services/<name>` | Obtener detalles de un microservicio |
| `PUT` | `/api/services/<name>/enable` | Habilitar un microservicio |
| `PUT` | `/api/services/<name>/disable` | Deshabilitar un microservicio |
| `DELETE` | `/api/services/<name>` | Eliminar un microservicio |
| `GET` | `/api/health` | Health check del backend |

**Conocimientos clave:**
- Python, Flask, Docker SDK for Python
- Manejo de procesos y archivos temporales
- API REST design

---

### 🎨 Persona 3: Oscar Gil — Frontend / Dashboard

**Rama:** `feature/frontend`

**Responsabilidades:**
- [ ] Dashboard web responsive con las siguientes secciones:
  - **Formulario de creación**: textarea para código, selector de lenguaje, campos de nombre y descripción
  - **Lista de microservicios**: tarjetas/tabla con nombre, estado, lenguaje, endpoint, acciones
  - **Acciones**: botones para habilitar, deshabilitar, eliminar, probar endpoint
- [ ] Consumir la API del backend vía `fetch()`
- [ ] Mostrar estados en tiempo real (creando, activo, deshabilitado, error)
- [ ] Feedback visual al usuario (loaders, notificaciones de éxito/error)
- [ ] Editor de código con resaltado básico (opcional: integrar CodeMirror o similar)
- [ ] Dockerfile del frontend (Nginx sirviendo archivos estáticos)

**Archivos principales:**
```
frontend/Dockerfile
frontend/src/index.html
frontend/src/app.js
frontend/src/styles.css
```

**Mockup del Dashboard:**

```
┌─────────────────────────────────────────────────────────────────┐
│  🚀 Plataforma de Microservicios UN                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ Crear Nuevo Microservicio ─────────────────────────────┐    │
│  │                                                          │    │
│  │  Nombre: [________________]  Lenguaje: [Python ▼]       │    │
│  │  Descripción: [________________________________]        │    │
│  │                                                          │    │
│  │  Código Fuente:                                          │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │ def process(data):                                │   │    │
│  │  │     name = data.get("name", "Mundo")             │   │    │
│  │  │     return {"message": f"Hola {name}!"}          │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │                          [ 🚀 Crear Microservicio ]      │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─ Microservicios Activos ────────────────────────────────┐    │
│  │                                                          │    │
│  │  🟢 hola-mundo    │ Python │ /services/hola-mundo       │    │
│  │     [Probar] [Deshabilitar] [Eliminar]                  │    │
│  │                                                          │    │
│  │  🟢 suma-valores  │ Node   │ /services/suma-valores     │    │
│  │     [Probar] [Deshabilitar] [Eliminar]                  │    │
│  │                                                          │    │
│  │  🔴 mi-servicio   │ Python │ /services/mi-servicio      │    │
│  │     [Probar] [Habilitar]   [Eliminar]                   │    │
│  │                                                          │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

**Conocimientos clave:**
- HTML5, CSS3, JavaScript (ES6+)
- Fetch API, DOM manipulation
- Diseño responsive
- UX/UI básico

---

### 🧪 Persona 4: Alberto Niebles — Templates, Testing & Documentación

**Rama:** `feature/templates-docs`

**Responsabilidades:**
- [ ] Crear los templates de Dockerfile para Python y Node.js
- [ ] Crear los wrappers que envuelven el código del usuario en un servidor HTTP
- [ ] Desarrollar los 4 ejemplos obligatorios (2 por lenguaje)
- [ ] Probar que los ejemplos funcionen correctamente end-to-end
- [ ] Documentar el README.md final con diagramas y guía de uso
- [ ] Grabar y editar el video de demostración en YouTube
- [ ] Testing de integración de la plataforma completa

**Archivos principales:**
```
templates/python/Dockerfile.template
templates/python/wrapper.py.template
templates/node/Dockerfile.template
templates/node/wrapper.js.template
templates/examples/python_hello.py
templates/examples/python_sum.py
templates/examples/node_hello.js
templates/examples/node_sum.js
```

**Conocimientos clave:**
- Docker, Dockerfiles
- Python (Flask básico), Node.js (Express básico)
- Documentación técnica, Markdown
- Edición de video

---

## 🌿 Estrategia de Ramas Git

### Modelo de Branching

```
main ─────────────────────────────────────────────────── (protegida, solo merges)
  │
  └── develop ──────────────────────────────────────────  (rama de integración)
        │
        ├── feature/infrastructure ──────── Jean         (Nginx, Docker Compose)
        │
        ├── feature/backend-api ─────────── Valentina    (API Flask, Docker SDK)
        │
        ├── feature/frontend ────────────── Oscar        (Dashboard HTML/JS)
        │
        └── feature/templates-docs ──────── Alberto      (Templates, ejemplos, docs)
```

### Reglas del Equipo

1. **Nunca hacer push directo a `main` ni a `develop`**
2. Cada persona trabaja **exclusivamente en su rama** `feature/*`
3. Para integrar cambios, crear un **Pull Request (PR)** hacia `develop`
4. Mínimo **1 persona debe revisar** el PR antes de hacer merge
5. Cuando `develop` esté estable y probado, se hace merge a `main`
6. Usar **commits descriptivos** con el formato:

```
tipo(alcance): descripción breve

Ejemplos:
feat(nginx): agregar configuración de reverse proxy
feat(backend): implementar endpoint POST /api/services
fix(frontend): corregir error al listar microservicios
docs(readme): actualizar diagrama de arquitectura
```

### Flujo de Trabajo con Git

```bash
# 1. Clonar el repositorio
git clone https://github.com/jeanmlq10/Microservices-platform-UN.git
cd Microservices-platform-UN

# 2. Cambiar a la rama develop
git checkout develop

# 3. Crear tu rama de trabajo (ejemplo para Jean)
git checkout -b feature/infrastructure

# 4. Trabajar, hacer commits
git add .
git commit -m "feat(nginx): configuración base del reverse proxy"

# 5. Subir tu rama
git push origin feature/infrastructure

# 6. Crear Pull Request en GitHub: feature/infrastructure → develop
```

---

## 📅 Cronograma de Trabajo

### Semana 1: Setup + Desarrollo Individual

| Día | Jean (Infra) | Valentina (Backend) | Oscar (Frontend) | Alberto (Templates) |
|-----|-------------------|----------------|-------------------|---------------------|
| **1-2** | `docker-compose.yml` base, red Docker, estructura de carpetas | Scaffold del backend Flask, Dockerfile | Estructura HTML base, Dockerfile | Templates Dockerfile para Python y Node.js |
| **3-4** | Config Nginx reverse proxy, rutas estáticas | Docker SDK: crear/eliminar contenedores | Formulario de creación de microservicios | Wrappers HTTP para Python (Flask) y Node.js (Express) |
| **5** | Mecanismo de recarga dinámica de Nginx | Endpoints CRUD completos | Lista de microservicios con acciones | 4 ejemplos funcionales listos |

### Semana 2: Integración + Testing + Entrega

| Día | Actividad | Responsable |
|-----|-----------|-------------|
| **6** | Merge de todas las ramas a `develop` | Todos |
| **7** | Pruebas de integración: crear microservicio desde dashboard | Todos |
| **8** | Fix de bugs de integración | Según área |
| **9** | Probar los 2 ejemplos obligatorios end-to-end | Alberto + Jean |
| **10** | README final, diagrama, grabación de video demo | Alberto (todos apoyan) |

---

## 🚀 Instalación y Ejecución

### Prerrequisitos

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)
- [Git](https://git-scm.com/)

### Levantar la plataforma

```bash
# 1. Clonar el repositorio
git clone https://github.com/jeanmlq10/Microservices-platform-UN.git
cd Microservices-platform-UN

# 2. Levantar toda la plataforma con un solo comando
docker-compose up --build

# 3. Abrir en el navegador
# http://localhost
```

### Detener la plataforma

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (limpieza total)
docker-compose down -v --remove-orphans
```

---

## 💻 Uso del Dashboard

### Crear un Microservicio

1. Abrir `http://localhost` en el navegador
2. En el formulario **"Crear Nuevo Microservicio"**:
   - Escribir un **nombre** (ej: `hola-mundo`)
   - Escribir una **descripción** (ej: `Mi primer microservicio`)
   - Seleccionar el **lenguaje** (Python o Node.js)
   - Pegar el **código fuente** en el textarea
3. Hacer clic en **"Crear Microservicio"**
4. Esperar a que el estado cambie a 🟢 **Activo**
5. El microservicio estará disponible en: `http://localhost/services/hola-mundo`

### Administrar Microservicios

- **Listar**: Todos los microservicios aparecen en la sección inferior del dashboard
- **Probar**: Clic en "Probar" para hacer una petición al endpoint
- **Deshabilitar**: Detiene el contenedor sin eliminarlo
- **Habilitar**: Reinicia un contenedor deshabilitado
- **Eliminar**: Elimina el contenedor y la imagen asociada

---

## 📝 Ejemplos Funcionales

> Los siguientes ejemplos están listos para **copiar y pegar** directamente en el dashboard.

### 🐍 Python — Hola Mundo

**Nombre:** `hola-mundo-python`
**Lenguaje:** Python

```python
def process(data):
    name = data.get("name", "Mundo")
    return {"message": f"Hola {name}!", "language": "Python"}
```

**Probar:**
```bash
# Sin parámetros
curl http://localhost/services/hola-mundo-python

# Con parámetros
curl http://localhost/services/hola-mundo-python?name=Universidad
```

**Respuesta esperada:**
```json
{
  "message": "Hola Universidad!",
  "language": "Python"
}
```

---

### 🐍 Python — Suma de Dos Valores

**Nombre:** `suma-python`
**Lenguaje:** Python

```python
def process(data):
    a = float(data.get("a", 0))
    b = float(data.get("b", 0))
    result = a + b
    return {"a": a, "b": b, "sum": result, "language": "Python"}
```

**Probar:**
```bash
curl "http://localhost/services/suma-python?a=15&b=27"
```

**Respuesta esperada:**
```json
{
  "a": 15.0,
  "b": 27.0,
  "sum": 42.0,
  "language": "Python"
}
```

---

### 🟢 Node.js — Hola Mundo

**Nombre:** `hola-mundo-node`
**Lenguaje:** Node.js

```javascript
function process(data) {
    const name = data.name || "Mundo";
    return { message: `Hola ${name}!`, language: "Node.js" };
}
module.exports = process;
```

**Probar:**
```bash
# Sin parámetros
curl http://localhost/services/hola-mundo-node

# Con parámetros
curl http://localhost/services/hola-mundo-node?name=Universidad
```

**Respuesta esperada:**
```json
{
  "message": "Hola Universidad!",
  "language": "Node.js"
}
```

---

### 🟢 Node.js — Suma de Dos Valores

**Nombre:** `suma-node`
**Lenguaje:** Node.js

```javascript
function process(data) {
    const a = parseFloat(data.a) || 0;
    const b = parseFloat(data.b) || 0;
    return { a: a, b: b, sum: a + b, language: "Node.js" };
}
module.exports = process;
```

**Probar:**
```bash
curl "http://localhost/services/suma-node?a=15&b=27"
```

**Respuesta esperada:**
```json
{
  "a": 15,
  "b": 27,
  "sum": 42,
  "language": "Node.js"
}
```

---

## 📡 API Reference

### Base URL: `http://localhost/api`

### Crear microservicio

```http
POST /api/services
Content-Type: application/json

{
  "name": "hola-mundo",
  "description": "Mi primer microservicio",
  "language": "python",
  "code": "def process(data):\n    return {\"message\": \"Hola Mundo!\"}"
}
```

**Response (201):**
```json
{
  "name": "hola-mundo",
  "status": "running",
  "language": "python",
  "endpoint": "/services/hola-mundo",
  "port": 9001,
  "created_at": "2026-03-11T10:30:00Z"
}
```

### Listar microservicios

```http
GET /api/services
```

**Response (200):**
```json
{
  "services": [
    {
      "name": "hola-mundo",
      "status": "running",
      "language": "python",
      "endpoint": "/services/hola-mundo",
      "port": 9001
    }
  ],
  "total": 1
}
```

### Obtener detalle de un microservicio

```http
GET /api/services/{name}
```

### Habilitar microservicio

```http
PUT /api/services/{name}/enable
```

### Deshabilitar microservicio

```http
PUT /api/services/{name}/disable
```

### Eliminar microservicio

```http
DELETE /api/services/{name}
```

### Health check

```http
GET /api/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "docker": "connected",
  "services_count": 3
}
```

---

## 🎥 Video de Demostración

> 📹 [Enlace al video en YouTube](#) *(pendiente de grabación)*

El video mostrará:
1. Levantamiento de la plataforma con `docker-compose up`
2. Creación de un microservicio "Hola Mundo" en Python
3. Creación de un microservicio "Suma" en Node.js
4. Prueba de los endpoints creados
5. Deshabilitación y eliminación de microservicios
6. Explicación breve de la arquitectura

---

## 🔩 ¿Cómo Funcionan los Templates Internamente?

Los templates son el mecanismo que convierte una **función simple del usuario** en un **microservicio Docker completo**. Sin ellos, el código que se pega en el dashboard sería solo texto sin ejecutar.

### El Problema

Cuando un usuario pega esto en el dashboard:

```python
def process(data):
    name = data.get("name", "Mundo")
    return {"message": f"Hola {name}!"}
```

Eso **no es un servidor HTTP**. Es solo una función suelta. No escucha peticiones, no responde JSON, no puede correr sola.

### La Solución: 3 Archivos por Lenguaje

| Archivo | Función |
|---------|---------|
| `Dockerfile.template` | Le dice a Docker **cómo construir la imagen**: qué base usar, qué instalar, qué ejecutar |
| `wrapper.py.template` / `wrapper.js.template` | Es un **servidor HTTP listo** (Flask o Express) que importa la función `process()` del usuario y la expone como endpoint |

### Flujo Interno Paso a Paso

```
1. Usuario pega código en el dashboard
   │
   ▼
2. Backend recibe el código vía POST /api/services
   │
   ▼
3. Backend crea un directorio temporal con 3 archivos:
   │
   │   directorio_temporal/
   │   ├── Dockerfile       ← copiado de Dockerfile.template
   │   ├── server.py        ← copiado de wrapper.py.template (servidor HTTP)
   │   └── user_code.py     ← el código que pegó el usuario
   │
   ▼
4. Backend ejecuta: docker build → crea imagen "ms-hola-mundo:latest"
   │
   ▼
5. Backend ejecuta: docker run → levanta contenedor en puerto 9001
   │
   ▼
6. Backend genera config de Nginx: /services/hola-mundo → contenedor:8080
   │
   ▼
7. Backend recarga Nginx → el microservicio ya es accesible
```

### ¿Qué hace el Wrapper?

El wrapper es el "pegamento". Toma la función `process()` del usuario y la envuelve en un servidor web:

**Para Python** (`wrapper.py.template`):
```python
# Importa la función del usuario
from user_code import process

@app.route("/")
def handle():
    data = request.args       # Recibe parámetros (?name=Mundo)
    result = process(data)    # Llama a la función del usuario
    return jsonify(result)    # Devuelve JSON
```

**Para Node.js** (`wrapper.js.template`):
```javascript
// Importa la función del usuario
const process = require("./user_code");

app.all("/", (req, res) => {
    const data = req.query;       // Recibe parámetros (?name=Mundo)
    const result = process(data); // Llama a la función del usuario
    res.json(result);             // Devuelve JSON
});
```

**Resultado final:** el usuario solo escribe una función `process(data)` → la plataforma genera todo lo demás automáticamente.

---

## 📚 Recursos Útiles

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Express.js Documentation](https://expressjs.com/)

---

## 📄 Licencia

Este proyecto es parte de una actividad académica de la **Universidad del Norte**.

---

<div align="center">

**Hecho con 🐳 Docker y ☕ mucho café**

*Universidad del Norte — Plataforma de Microservicios — 2026*

</div>
