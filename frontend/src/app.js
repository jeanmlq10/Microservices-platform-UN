/**
 * app.js - Logica del Dashboard de Microservicios
 * Consume la API del backend para crear, listar, habilitar, deshabilitar y eliminar microservicios.
 */

const API_BASE = "/api";

const createForm = document.getElementById("create-form");
const servicesList = document.getElementById("services-list");
const createStatus = document.getElementById("create-status");
const btnCreate = document.getElementById("btn-create");
const testSection = document.getElementById("test-section");
const testUrl = document.getElementById("test-url");
const testParams = document.getElementById("test-params");
const btnTest = document.getElementById("btn-test");
const testResult = document.getElementById("test-result");

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function normalizeErrorMessage(message) {
    const lines = String(message || "")
        .split("\n")
        .map(line => line.trimEnd())
        .filter(line => line.trim() !== "");

    return {
        summary: lines[0] || "Ocurrio un error inesperado.",
        details: lines.slice(1).join("\n")
    };
}

async function readJson(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}

function showStatus(message, type) {
    const payload = typeof message === "string"
        ? normalizeErrorMessage(message)
        : {
            summary: message.summary || "",
            details: message.details || ""
        };

    const detailHtml = payload.details
        ? `<pre class="status-details">${escapeHtml(payload.details)}</pre>`
        : "";

    createStatus.innerHTML = `
        <div class="status-summary">${escapeHtml(payload.summary)}</div>
        ${detailHtml}
    `;
    createStatus.className = `status-message ${type}`;
    createStatus.classList.remove("hidden");

    if (type === "success" || type === "info") {
        setTimeout(() => createStatus.classList.add("hidden"), 5000);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadServices();
});

createForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("service-name").value.trim();
    const language = document.getElementById("service-language").value;
    const description = document.getElementById("service-description").value.trim();
    const code = document.getElementById("service-code").value;

    if (!name || !code) {
        showStatus("Por favor completa nombre y codigo.", "error");
        return;
    }

    btnCreate.disabled = true;
    btnCreate.textContent = "Creando...";
    showStatus({
        summary: "Construyendo imagen Docker y levantando contenedor...",
        details: "La plataforma validara el contenedor antes de publicarlo."
    }, "info");

    try {
        const response = await fetch(`${API_BASE}/services`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, language, description, code })
        });

        const data = await readJson(response);

        if (response.ok) {
            showStatus({
                summary: `Microservicio '${name}' creado exitosamente.`,
                details: `Endpoint disponible en ${data.endpoint}`
            }, "success");
            createForm.reset();
            loadServices();
        } else {
            showStatus(normalizeErrorMessage(data.error), "error");
        }
    } catch (err) {
        showStatus({
            summary: "Error de conexion con el backend.",
            details: err.message
        }, "error");
    } finally {
        btnCreate.disabled = false;
        btnCreate.textContent = "Crear Microservicio";
    }
});

async function loadServices() {
    try {
        const response = await fetch(`${API_BASE}/services`);
        const data = await readJson(response);

        if (!data.services || data.services.length === 0) {
            servicesList.innerHTML = '<p class="empty-state">No hay microservicios creados aun. Crea el primero.</p>';
            return;
        }

        servicesList.innerHTML = data.services.map(service => `
            <div class="service-card ${service.status === "running" ? "running" : "stopped"}">
                <div class="service-info">
                    <span class="status-dot ${service.status === "running" ? "dot-green" : "dot-red"}"></span>
                    <strong>${service.name}</strong>
                    <span class="badge badge-${service.language}">${service.language === "python" ? "Python" : "Node.js"}</span>
                    <code>${service.endpoint}</code>
                    <span class="service-desc">${service.description || ""}</span>
                </div>
                <div class="service-actions">
                    <button class="btn-small btn-test" onclick="openTest('${service.name}', '${service.endpoint}')">Probar</button>
                    ${service.status === "running"
                        ? `<button class="btn-small btn-disable" onclick="disableService('${service.name}')">Deshabilitar</button>`
                        : `<button class="btn-small btn-enable" onclick="enableService('${service.name}')">Habilitar</button>`
                    }
                    <button class="btn-small btn-delete" onclick="deleteService('${service.name}')">Eliminar</button>
                </div>
            </div>
        `).join("");
    } catch {
        servicesList.innerHTML = '<p class="error-state">No se pudieron cargar los microservicios.</p>';
    }
}

async function enableService(name) {
    try {
        const response = await fetch(`${API_BASE}/services/${name}/enable`, { method: "PUT" });
        const data = await readJson(response);

        if (response.ok) {
            showStatus({ summary: `Microservicio '${name}' habilitado.`, details: "" }, "success");
            loadServices();
            return;
        }

        showStatus(normalizeErrorMessage(data.error), "error");
    } catch (err) {
        showStatus({
            summary: `No se pudo habilitar '${name}'.`,
            details: err.message
        }, "error");
    }
}

async function disableService(name) {
    try {
        const response = await fetch(`${API_BASE}/services/${name}/disable`, { method: "PUT" });
        const data = await readJson(response);

        if (response.ok) {
            showStatus({ summary: `Microservicio '${name}' deshabilitado.`, details: "" }, "info");
            loadServices();
            return;
        }

        showStatus(normalizeErrorMessage(data.error), "error");
    } catch (err) {
        showStatus({
            summary: `No se pudo deshabilitar '${name}'.`,
            details: err.message
        }, "error");
    }
}

async function deleteService(name) {
    if (!confirm(`Estas seguro de eliminar el microservicio '${name}'?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/services/${name}`, { method: "DELETE" });
        const data = await readJson(response);

        if (response.ok) {
            showStatus({ summary: `Microservicio '${name}' eliminado.`, details: "" }, "success");
            loadServices();
            testSection.classList.add("hidden");
            return;
        }

        showStatus(normalizeErrorMessage(data.error), "error");
    } catch (err) {
        showStatus({
            summary: `No se pudo eliminar '${name}'.`,
            details: err.message
        }, "error");
    }
}

function openTest(_name, endpoint) {
    testSection.classList.remove("hidden");
    testUrl.value = endpoint;
    testParams.value = "";
    testResult.textContent = "// Haz clic en 'Ejecutar' para probar el endpoint";
    testSection.scrollIntoView({ behavior: "smooth" });
}

btnTest.addEventListener("click", async () => {
    const url = testUrl.value;
    const params = testParams.value.trim();
    const fullUrl = params ? `${url}?${params}` : url;

    testResult.textContent = "Ejecutando...";

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
        testResult.textContent = `Error: ${err.message}`;
    }
});
