/**
 * app.js - Lógica del Dashboard de Microservicios
 * Consume la API del backend para crear, listar, habilitar, deshabilitar y eliminar microservicios.
 */

const API_BASE = "/api";

// ─── Elementos del DOM ───
const createForm = document.getElementById("create-form");
const servicesList = document.getElementById("services-list");
const createStatus = document.getElementById("create-status");
const btnCreate = document.getElementById("btn-create");
const testSection = document.getElementById("test-section");
const testUrl = document.getElementById("test-url");
const testParams = document.getElementById("test-params");
const btnTest = document.getElementById("btn-test");
const testResult = document.getElementById("test-result");

// ─── Cargar microservicios al iniciar ───
document.addEventListener("DOMContentLoaded", () => {
    loadServices();
});

// ─── Crear microservicio ───
createForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("service-name").value.trim();
    const language = document.getElementById("service-language").value;
    const description = document.getElementById("service-description").value.trim();
    const code = document.getElementById("service-code").value;

    if (!name || !code) {
        showStatus("Por favor completa nombre y código", "error");
        return;
    }

    btnCreate.disabled = true;
    btnCreate.textContent = "⏳ Creando...";
    showStatus("Construyendo imagen Docker y levantando contenedor...", "info");

    try {
        const response = await fetch(`${API_BASE}/services`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, language, description, code })
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(`✅ Microservicio '${name}' creado exitosamente en ${data.endpoint}`, "success");
            createForm.reset();
            loadServices();
        } else {
            showStatus(`❌ Error: ${data.error}`, "error");
        }
    } catch (err) {
        showStatus(`❌ Error de conexión: ${err.message}`, "error");
    } finally {
        btnCreate.disabled = false;
        btnCreate.textContent = "🚀 Crear Microservicio";
    }
});

// ─── Cargar lista de microservicios ───
async function loadServices() {
    try {
        const response = await fetch(`${API_BASE}/services`);
        const data = await response.json();

        if (data.services.length === 0) {
            servicesList.innerHTML = '<p class="empty-state">No hay microservicios creados aún. ¡Crea el primero! 👆</p>';
            return;
        }

        servicesList.innerHTML = data.services.map(service => `
            <div class="service-card ${service.status === 'running' ? 'running' : 'stopped'}">
                <div class="service-info">
                    <span class="status-dot ${service.status === 'running' ? 'dot-green' : 'dot-red'}"></span>
                    <strong>${service.name}</strong>
                    <span class="badge badge-${service.language}">${service.language === 'python' ? '🐍 Python' : '🟢 Node.js'}</span>
                    <code>${service.endpoint}</code>
                    <span class="service-desc">${service.description || ''}</span>
                </div>
                <div class="service-actions">
                    <button class="btn-small btn-test" onclick="openTest('${service.name}', '${service.endpoint}')">🧪 Probar</button>
                    ${service.status === 'running'
                        ? `<button class="btn-small btn-disable" onclick="disableService('${service.name}')">⏸️ Deshabilitar</button>`
                        : `<button class="btn-small btn-enable" onclick="enableService('${service.name}')">▶️ Habilitar</button>`
                    }
                    <button class="btn-small btn-delete" onclick="deleteService('${service.name}')">🗑️ Eliminar</button>
                </div>
            </div>
        `).join("");

    } catch (err) {
        servicesList.innerHTML = '<p class="error-state">❌ Error al cargar microservicios</p>';
    }
}

// ─── Habilitar microservicio ───
async function enableService(name) {
    try {
        const response = await fetch(`${API_BASE}/services/${name}/enable`, { method: "PUT" });
        if (response.ok) loadServices();
    } catch (err) {
        alert(`Error al habilitar: ${err.message}`);
    }
}

// ─── Deshabilitar microservicio ───
async function disableService(name) {
    try {
        const response = await fetch(`${API_BASE}/services/${name}/disable`, { method: "PUT" });
        if (response.ok) loadServices();
    } catch (err) {
        alert(`Error al deshabilitar: ${err.message}`);
    }
}

// ─── Eliminar microservicio ───
async function deleteService(name) {
    if (!confirm(`¿Estás seguro de eliminar el microservicio '${name}'?`)) return;

    try {
        const response = await fetch(`${API_BASE}/services/${name}`, { method: "DELETE" });
        if (response.ok) {
            loadServices();
            testSection.classList.add("hidden");
        }
    } catch (err) {
        alert(`Error al eliminar: ${err.message}`);
    }
}

// ─── Abrir panel de prueba ───
function openTest(name, endpoint) {
    testSection.classList.remove("hidden");
    testUrl.value = endpoint;
    testParams.value = "";
    testResult.textContent = "// Haz clic en 'Ejecutar' para probar el endpoint";
    testSection.scrollIntoView({ behavior: "smooth" });
}

// ─── Ejecutar prueba ───
btnTest.addEventListener("click", async () => {
    const url = testUrl.value;
    const params = testParams.value.trim();
    const fullUrl = params ? `${url}?${params}` : url;

    testResult.textContent = "⏳ Ejecutando...";

    try {
        const response = await fetch(fullUrl);
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const text = await response.text();
            testResult.textContent = `❌ Error ${response.status}: El microservicio no responde con JSON.\n\n${text}`;
            return;
        }
        const data = await response.json();
        testResult.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        testResult.textContent = `❌ Error: ${err.message}`;
    }
});

// ─── Mostrar mensaje de estado ───
function showStatus(message, type) {
    createStatus.textContent = message;
    createStatus.className = `status-message ${type}`;
    createStatus.classList.remove("hidden");

    if (type === "success") {
        setTimeout(() => createStatus.classList.add("hidden"), 5000);
    }
}
