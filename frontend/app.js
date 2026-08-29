const ENV_API_BASE = (window.__APP_API_BASE__ || "").replace(/\/$/, "");
const API_BASE = ENV_API_BASE || (window.location.port === "5173" ? "http://127.0.0.1:8000" : "");

const machineSelect = document.querySelector("#machine-select");
const machineCard = document.querySelector("#machine-card");
const questionInput = document.querySelector("#question-input");
const chatForm = document.querySelector("#chat-form");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-button");
const conversation = document.querySelector("#conversation");
const evidenceContent = document.querySelector("#evidence-content");
const sourceCount = document.querySelector("#source-count");
const connectionLabel = document.querySelector("#connection-label");
const stateDot = document.querySelector(".state-dot");
const inputHint = document.querySelector("#input-hint");
const toast = document.querySelector("#toast");

let machines = [];
let toastTimer;

function apiUrl(path) { return `${API_BASE}${path}`; }

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 4200);
}

function setConnection(ready, label) {
  stateDot.classList.toggle("ready", ready);
  connectionLabel.textContent = label;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

function updateMachineCard(machine) {
  if (!machine) {
    machineCard.className = "machine-card empty-card";
    machineCard.textContent = "Select a machine to load its context.";
    sendButton.disabled = true;
    inputHint.textContent = "Select a machine to begin";
    return;
  }
  machineCard.className = "machine-card";
  machineCard.innerHTML = `<strong>${escapeHtml(machine.machine_code)}</strong><span>${escapeHtml(machine.name)}</span><span>${escapeHtml(machine.machine_type)} · ${escapeHtml(machine.location || "Location unavailable")}</span><span>Status: ${escapeHtml(machine.status)}</span>`;
  sendButton.disabled = !questionInput.value.trim();
  inputHint.textContent = "Evidence-backed answers only";
}

async function loadMachines() {
  try {
    const response = await fetch(apiUrl("/api/machines"));
    if (!response.ok) throw new Error("Machine register unavailable");
    machines = await response.json();
    machineSelect.innerHTML = machines.length ? machines.map(machine => `<option value="${machine.id}">${escapeHtml(machine.machine_code)} · ${escapeHtml(machine.name)}</option>`).join("") : "<option value="">No machines registered</option>";
    machineSelect.disabled = !machines.length;
    updateMachineCard(machines[0]);
    setConnection(true, "Control plane connected");
  } catch (error) {
    machineSelect.innerHTML = "<option value="">Machine register unavailable</option>";
    machineSelect.disabled = true;
    setConnection(false, "Backend unavailable");
    showToast("Could not load the machine register. Start the backend and try again.");
  }
}

function addUserMessage(question) {
  conversation.insertAdjacentHTML("beforeend", `<article class="message user"><div class="message-label">Technician query</div><div class="message-body">${escapeHtml(question)}</div></article>`);
  conversation.scrollTop = conversation.scrollHeight;
}

function addAnswerMessage(payload) {
  const answer = payload.answer || {};
  const uncertain = answer.insufficient_information;
  const lists = [
    ["Possible causes", answer.possible_causes],
    ["Recommended actions", answer.recommended_actions],
    ["Safety considerations", answer.safety_considerations]
  ].filter(([, values]) => values?.length).map(([title, values]) => `<div class="answer-title">${title}</div><ul class="answer-list">${values.map(value => `<li>${escapeHtml(value)}</li>`).join("")}</ul>`).join("");
  conversation.insertAdjacentHTML("beforeend", `<article class="message"><div class="message-label">Assistant · ${uncertain ? "Insufficient evidence" : "Grounded guidance"}</div><div class="message-body answer-card ${uncertain ? "uncertain" : ""}"><div class="answer-title">${uncertain ? "Evidence is limited" : "Maintenance guidance"}</div><div>${escapeHtml(answer.assessment || "No answer was returned.")}</div>${lists}</div></article>`);
  conversation.scrollTop = conversation.scrollHeight;
}

function renderSources(sources) {
  sourceCount.textContent = sources.length;
  if (!sources.length) {
    evidenceContent.innerHTML = "<div class=\"evidence-empty\"><span class=\"empty-icon\">+</span><p>No document sources were used for this answer.</p></div>";
    return;
  }
  evidenceContent.innerHTML = sources.map((source, index) => {
    const title = source.document_name || source.source || source.document_id || "Verified evidence";
    const meta = [source.chunk_id && `Chunk ${source.chunk_id}`, source.section && `Section ${source.section}`, source.page && `Page ${source.page}`, source.score !== undefined && `Relevance ${Number(source.score).toFixed(2)}`].filter(Boolean).join(" · ");
    return `<div class="source-item"><div class="source-name">${String(index + 1).padStart(2, "0")} / ${escapeHtml(title)}</div><div class="source-meta">${escapeHtml(meta || "Metadata unavailable")}</div></div>`;
  }).join("");
}

function errorMessage(response, payload) {
  if (response.status === 404) return "That machine could not be found in the register.";
  if (response.status === 422) return "Check the machine selection and enter a maintenance question.";
  return payload?.detail || "The maintenance assistant is temporarily unavailable.";
}

async function askAssistant(event) {
  event.preventDefault();
  const question = questionInput.value.trim();
  const machineId = Number(machineSelect.value);
  if (!question) { showToast("Enter a maintenance question first."); questionInput.focus(); return; }
  if (!machineId) { showToast("Select a machine first."); return; }
  addUserMessage(question);
  questionInput.value = "";
  sendButton.disabled = true;
  sendButton.querySelector("span").textContent = "Working...";
  inputHint.textContent = "Retrieving maintenance evidence...";
  const loading = document.createElement("article");
  loading.className = "message";
  loading.innerHTML = '<div class="message-label">Assistant</div><div class="message-body">Reviewing machine context and indexed evidence...</div>';
  conversation.appendChild(loading);
  conversation.scrollTop = conversation.scrollHeight;
  try {
    const response = await fetch(apiUrl("/api/chat"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ machine_id: machineId, question, top_k: 5 }) });
    const payload = await response.json().catch(() => ({}));
    loading.remove();
    if (!response.ok) throw new Error(errorMessage(response, payload));
    addAnswerMessage(payload);
    renderSources(payload.sources || []);
    setConnection(true, "Control plane connected");
  } catch (error) {
    loading.remove();
    showToast(error.message || "Unable to reach the maintenance assistant.");
    setConnection(false, "Assistant connection issue");
  } finally {
    sendButton.querySelector("span").textContent = "Ask assistant";
    sendButton.disabled = !machineSelect.value || !questionInput.value.trim();
    inputHint.textContent = machineSelect.value ? "Evidence-backed answers only" : "Select a machine to begin";
  }
}

machineSelect.addEventListener("change", () => updateMachineCard(machines.find(machine => machine.id === Number(machineSelect.value))));
questionInput.addEventListener("input", () => { sendButton.disabled = !machineSelect.value || !questionInput.value.trim(); });
questionInput.addEventListener("keydown", event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); chatForm.requestSubmit(); } });
chatForm.addEventListener("submit", askAssistant);
clearButton.addEventListener("click", () => { conversation.innerHTML = '<div class="welcome-message"><span class="welcome-index">01</span><div><h3>What needs attention?</h3><p>Ask about readings, vibration, procedures, or a suspected fault. Select a machine first so the answer has the right operating context.</p></div></div>'; renderSources([]); });
loadMachines();
