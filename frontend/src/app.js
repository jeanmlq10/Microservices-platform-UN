/**
 * app.js - Lógica del Dashboard de Microservicios
 * Consume la API del backend para crear, listar, habilitar, deshabilitar y eliminar microservicios.
 */

const API_BASE = "/api";

// ══════════════════════════════════════════════════════════
//  UTILIDADES
// ══════════════════════════════════════════════════════════

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<​", "&lt;")
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
        summary: lines[0] || "Ocurrió un error inesperado.",
        details: lines.slice(1).join("\n")
    };
}

async function readJson(response) {
    try { return await response.json(); }
    catch { return {}; }
}

function showStatus(message, type) {
    const payload = typeof message === "string"
        ? normalizeErrorMessage(message)
        : { summary: message.summary || "", details: message.details || "" };

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

// ══════════════════════════════════════════════════════════
//  EDITOR DE CÓDIGO — CodeMirror 5
// ══════════════════════════════════════════════════════════

const TEMPLATES = {
    python: `from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def handler():
    name = request.args.get("name", "Mundo")
    return jsonify({"message": f"Hola, {name}!", "status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
`,
    node: `const express = require("express");
const app = express();

app.get("/", (req, res) => {
    const name = req.query.name || "Mundo";
    res.json({ message: \`Hola, \${name}!\`, status: "ok" });
});

app.listen(3000, () => console.log("Servidor corriendo en puerto 3000"));
`
};

const LANG_ICONS = {
    python: document.getElementById("lang-icon-python"),
    node: document.getElementById("lang-icon-node")
};

const codeEditor = CodeMirror(document.getElementById("code-editor"), {
    mode: "python",
    theme: "dracula",
    lineNumbers: true,
    matchBrackets: true,
    autoCloseBrackets: true,
    styleActiveLine: true,
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    lineWrapping: false,
    extraKeys: {
        "Tab": (cm) => cm.execCommand("indentMore"),
        "Shift-Tab": (cm) => cm.execCommand("indentLess"),
        "Ctrl-/": (cm) => cm.execCommand("toggleComment"),
    },
    value: TEMPLATES.python
});

const hiddenTextarea = document.getElementById("service-code");
hiddenTextarea.value = codeEditor.getValue();

codeEditor.on("change", (cm) => {
    hiddenTextarea.value = cm.getValue();
    updateStatusBar(cm);
});
codeEditor.on("cursorActivity", (cm) => updateStatusBar(cm));

function updateStatusBar(cm) {
    const cursor = cm.getCursor();
    document.getElementById("editor-line").textContent = cursor.line + 1;
    document.getElementById("editor-col").textContent = cursor.ch + 1;
    document.getElementById("editor-chars").textContent = `${cm.getValue().length} caracteres`;
}

// Cambiar lenguaje del editor
document.getElementById("service-language").addEventListener("change", function () {
    const lang = this.value;
    const isPython = lang === "python";

    codeEditor.setOption("mode", isPython ? "python" : "javascript");
    document.getElementById("editor-lang-text").textContent = isPython ? "Python" : "Node.js";
    document.getElementById("editor-mode-label").textContent = isPython ? "Python" : "JavaScript";

    // Alternar icono SVG
    LANG_ICONS.python.style.display = isPython ? "block" : "none";
    LANG_ICONS.node.style.display = isPython ? "none" : "block";

    // Cargar plantilla si el editor está vacío o tiene la plantilla anterior
    const currentVal = codeEditor.getValue().trim();
    const prevTemplate = TEMPLATES[isPython ? "node" : "python"].trim();
    if (currentVal === "" || currentVal === prevTemplate) {
        codeEditor.setValue(TEMPLATES[lang]);
    }
});

// Botón: Copiar
document.getElementById("btn-copy-code").addEventListener("click", () => {
    navigator.clipboard.writeText(codeEditor.getValue()).then(() => {
        const btn = document.getElementById("btn-copy-code");
        const prev = btn.innerHTML;
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none"><polyline points="20 6 9 17 4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg> Copiado`;
        setTimeout(() => btn.innerHTML = prev, 1500);
    });
});

// Botón: Limpiar
document.getElementById("btn-clear-code").addEventListener("click", () => {
    if (confirm("¿Limpiar el editor?")) {
        codeEditor.setValue("");
        codeEditor.focus();
    }
});

// Botón: Plantilla
document.getElementById("btn-template").addEventListener("click", () => {
    const lang = document.getElementById("service-language").value;
    codeEditor.setValue(TEMPLATES[lang]);
    codeEditor.focus();
});

// ══════════════════════════════════════════════════════════
//  ELEMENTOS DEL DOM
// ══════════════════════════════════════════════════════════

const createForm = document.getElementById("create-form");
const servicesList = document.getElementById("services-list");
const createStatus = document.getElementById("create-status");
const btnCreate = document.getElementById("btn-create");
const testSection = document.getElementById("test-section");
const testUrl = document.getElementById("test-url");
const testParams = document.getElementById("test-params");
const btnTest = document.getElementById("btn-test");
const testResult = document.getElementById("test-result");

// ══════════════════════════════════════════════════════════
//  LÓGICA DE LA API
// ══════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => { loadServices(); });

// ─── Crear microservicio ───
createForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("service-name").value.trim();
    const language = document.getElementById("service-language").value;
    const description = document.getElementById("service-description").value.trim();
    const code = codeEditor.getValue();

    if (!name || !code.trim()) {
        showStatus("Por favor completa nombre y código.", "error");
        return;
    }

    btnCreate.disabled = true;
    btnCreate.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-dasharray="31.4" stroke-dashoffset="10"><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="0.8s" repeatCount="indefinite"/></circle></svg> Creando...`;

    showStatus({
        summary: "Construyendo imagen Docker y levantando contenedor...",
        details: "La plataforma validará el contenedor antes de publicarlo."
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
            codeEditor.setValue(TEMPLATES[language]);
            loadServices();
        } else {
            showStatus(normalizeErrorMessage(data.error), "error");
        }
    } catch (err) {
        showStatus({ summary: "Error de conexión con el backend.", details: err.message }, "error");
    } finally {
        btnCreate.disabled = false;
        btnCreate.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg> Crear Microservicio`;
    }
});

// ─── Cargar lista de microservicios ───
async function loadServices() {
    try {
        const response = await fetch(`${API_BASE}/services`);
        const data = await readJson(response);

        if (!data.services || data.services.length === 0) {
            servicesList.innerHTML = '<p class="empty-state">No hay microservicios creados aún. ¡Crea el primero!</p>';
            return;
        }

        const pythonSvg = `<svg width="12" height="12" viewBox="0 0 256 255" xmlns="http://www.w3.org/2000/svg"><path d="M126.9 0C62.1 0 66 28.3 66 28.3l.1 29.3h62v8.8H41.2S0 61.5 0 127c0 65.4 36.2 63.1 36.2 63.1h21.6v-30.4s-1.2-36.2 35.6-36.2h61.3s34.4.6 34.4-33.3V34.4S194.6 0 126.9 0zm-34 19.6c6.2 0 11.2 5 11.2 11.2s-5 11.2-11.2 11.2-11.2-5-11.2-11.2 5-11.2 11.2-11.2z" fill="#3776ab"/><path d="M129.1 255c64.8 0 60.9-28.3 60.9-28.3l-.1-29.3h-62v-8.8h86.9S256 193.5 256 128c0-65.4-36.2-63.1-36.2-63.1h-21.6v30.4s1.2 36.2-35.6 36.2h-61.3S67 130.9 67 164.8v62.8S61.4 255 129.1 255zm34-19.6c-6.2 0-11.2-5-11.2-11.2s5-11.2 11.2-11.2 11.2 5 11.2 11.2-5 11.2-11.2 11.2z" fill="#ffd43b"/></svg>`;
        const nodeSvg = `<svg width="12" height="12" viewBox="0 0 256 289" xmlns="http://www.w3.org/2000/svg"><path d="M128 0L0 72v144l128 72 128-72V72L128 0z" fill="#539e43"/><path d="M110 168c0 10 7 17 18 17s18-7 18-17v-52h-12v51c0 4-2 6-6 6s-6-2-6-6v-3h-12v4z" fill="#fff"/></svg>`;

        servicesList.innerHTML = data.services.map(service => `
            <div class="service-card ${service.status === "running" ? "running" : "stopped"}">
                <div class="service-info">
                    <span class="status-dot ${service.status === "running" ? "dot-green" : "dot-red"}"></span>
                    <strong>${escapeHtml(service.name)}</strong>
                    <span class="badge badge-${service.language}">
                        ${service.language === "python" ? pythonSvg : nodeSvg}
                        ${service.language === "python" ? "Python" : "Node.js"}
                    </span>
                    <code>${escapeHtml(service.endpoint)}</code>
                    <span class="service-desc">${escapeHtml(service.description || "")}</span>
                </div>
                <div class="service-actions">
                    <button class="btn-small btn-test-svc" onclick="openTest('${escapeHtml(service.name)}', '${escapeHtml(service.endpoint)}')">▶ Probar</button>
                    ${service.status === "running"
                ? `<button class="btn-small btn-disable" onclick="disableService('${escapeHtml(service.name)}')">⏸ Deshabilitar</button>`
                : `<button class="btn-small btn-enable"  onclick="enableService('${escapeHtml(service.name)}')">▶ Habilitar</button>`
            }
                    <button class="btn-small btn-delete" onclick="deleteService('${escapeHtml(service.name)}')">✕ Eliminar</button>
                </div>
            </div>
        `).join("");
    } catch {
        servicesList.innerHTML = '<p class="error-state">No se pudieron cargar los microservicios.</p>';
    }
}

// ─── Habilitar ───
async function enableService(name) {
    try {
        const response = await fetch(`${API_BASE}/services/${name}/enable`, { method: "PUT" });
        const data = await readJson(response);
        if (response.ok) { showStatus({ summary: `Microservicio '${name}' habilitado.`, details: "" }, "success"); loadServices(); return; }
        showStatus(normalizeErrorMessage(data.error), "error");
    } catch (err) {
        showStatus({ summary: `No se pudo habilitar '${name}'.`, details: err.message }, "error");
    }
}

// ─── Deshabilitar ───
async function disableService(name) {
    try {
        const response = await fetch(`${API_BASE}/services/${name}/disable`, { method: "PUT" });
        const data = await readJson(response);
        if (response.ok) { showStatus({ summary: `Microservicio '${name}' deshabilitado.`, details: "" }, "info"); loadServices(); return; }
        showStatus(normalizeErrorMessage(data.error), "error");
    } catch (err) {
        showStatus({ summary: `No se pudo deshabilitar '${name}'.`, details: err.message }, "error");
    }
}

// ─── Eliminar ───
async function deleteService(name) {
    if (!confirm(`¿Estás seguro de eliminar el microservicio '${name}'?`)) return;
    try {
        const response = await fetch(`${API_BASE}/services/${name}`, { method: "DELETE" });
        const data = await readJson(response);
        if (response.ok) { showStatus({ summary: `Microservicio '${name}' eliminado.`, details: "" }, "success"); loadServices(); testSection.classList.add("hidden"); return; }
        showStatus(normalizeErrorMessage(data.error), "error");
    } catch (err) {
        showStatus({ summary: `No se pudo eliminar '${name}'.`, details: err.message }, "error");
    }
}

// ─── Abrir panel de prueba ───
function openTest(_name, endpoint) {
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