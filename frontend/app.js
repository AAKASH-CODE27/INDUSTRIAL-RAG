/**
 * ForgeLine Industrial Maintenance Assistant Frontend Logic
 * Robust async implementation with centralized API configuration,
 * comprehensive timeout/error handling, and zero dependencies.
 */

// 1. Centralized API Configuration
function getApiBase() {
  if (window.__APP_API_BASE__) {
    return window.__APP_API_BASE__.replace(/\/$/, "");
  }

  // If served directly by FastAPI under /app or same origin (production or local backend)
  if (
    window.location.protocol.startsWith("http") &&
    window.location.port !== "5173" &&
    window.location.port !== "3000" &&
    window.location.port !== "8080"
  ) {
    // If the host is Render production or local backend serving static files
    if (window.location.hostname.includes("onrender.com")) {
      return window.location.origin;
    }
    if (window.location.port === "8000") {
      return "http://127.0.0.1:8000";
    }
  }

  // If running locally on a dev port like 5173, point to local backend
  if (window.location.port === "5173") {
    return "http://127.0.0.1:8000";
  }

  // Fallback to deployed production API
  return "https://industrial-rag.onrender.com";
}

const API_BASE = getApiBase();
const DEFAULT_TIMEOUT_MS = 35000;

// DOM Elements
const machineSelect = document.querySelector("#machine-select");
const machineCard = document.querySelector("#machine-card");
const retryMachinesButton = document.querySelector("#retry-machines-button");
const questionInput = document.querySelector("#question-input");
const chatForm = document.querySelector("#chat-form");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-button");
const globalRefreshButton = document.querySelector("#global-refresh-button");
const conversation = document.querySelector("#conversation");
const evidenceContent = document.querySelector("#evidence-content");
const sourceCount = document.querySelector("#source-count");
const confidenceBanner = document.querySelector("#confidence-banner");
const connectionLabel = document.querySelector("#connection-label");
const stateDot = document.querySelector(".state-dot");
const inputHint = document.querySelector("#input-hint");
const toast = document.querySelector("#toast");

// Application State
let machines = [];
let selectedMachineId = null;
let toastTimer = null;
let isSubmitting = false;

/**
 * Robust fetch wrapper with timeout and standardized error handling
 */
async function apiFetch(endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const url = `${API_BASE}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      const timeoutError = new Error("Request timed out. Please try again.");
      timeoutError.status = 408;
      throw timeoutError;
    }
    const networkError = new Error("Backend unavailable. Please verify the API connection and try again.");
    networkError.status = 0;
    networkError.originalError = err;
    throw networkError;
  }
}

/**
 * Toast notification
 */
function showToast(message, isError = false) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 4500);
}

/**
 * Update Connection Indicator
 * States: 'connecting', 'connected', 'error'
 */
function setConnectionState(state, label) {
  stateDot.classList.remove("ready", "error");
  if (state === "connected") {
    stateDot.classList.add("ready");
    connectionLabel.textContent = label || "Control plane connected";
  } else if (state === "error") {
    stateDot.classList.add("error");
    connectionLabel.textContent = label || "Backend unavailable";
  } else {
    // connecting
    connectionLabel.textContent = label || "Connecting to control plane...";
  }
}

/**
 * Safe HTML escape helper
 */
function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>'"]/g,
    character =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&#39;",
        '"': "&quot;",
      }[character])
  );
}

/**
 * Update the left machine info card
 */
function updateMachineCard(machine) {
  if (!machine) {
    machineCard.className = "machine-card empty-card";
    machineCard.textContent = "Select a machine to load its context.";
    validateForm();
    return;
  }

  selectedMachineId = machine.id;
  machineCard.className = "machine-card";
  machineCard.innerHTML = `
    <strong>${escapeHtml(machine.machine_code)}</strong>
    <span class="machine-subtitle">${escapeHtml(machine.name)}</span>
    <span class="machine-meta">${escapeHtml(machine.machine_type)} &middot; ${escapeHtml(machine.location || "Location unavailable")}</span>
    <span class="machine-status">${escapeHtml(machine.status || "Operational")}</span>
  `;

  validateForm();
}

/**
 * Form validation: manages Send button and hints
 */
function validateForm() {
  const hasMachine = Boolean(selectedMachineId && machineSelect.value);
  const hasText = Boolean(questionInput.value.trim());

  if (isSubmitting) {
    sendButton.disabled = true;
    return;
  }

  if (!hasMachine) {
    sendButton.disabled = true;
    inputHint.textContent = "Select a machine to begin";
  } else if (!hasText) {
    sendButton.disabled = true;
    inputHint.textContent = "Enter a maintenance question";
  } else {
    sendButton.disabled = false;
    inputHint.textContent = "Evidence-backed answers only";
  }
}

/**
 * Load machine list from GET /api/machines
 */
async function loadMachines() {
  setConnectionState("connecting", "Connecting to control plane...");
  machineSelect.disabled = true;
  machineSelect.innerHTML = `<option value="">Loading machine register...</option>`;
  retryMachinesButton.classList.add("hidden");

  try {
    const response = await apiFetch("/api/machines", { method: "GET" });

    if (!response.ok) {
      throw new Error(`Machine register responded with status ${response.status}`);
    }

    const data = await response.json();
    if (!Array.isArray(data)) {
      throw new Error("Invalid response format received from machines API");
    }

    machines = data;

    if (machines.length === 0) {
      machineSelect.innerHTML = `<option value="">No machines registered</option>`;
      machineSelect.disabled = true;
      updateMachineCard(null);
      setConnectionState("connected", "Control plane connected (0 machines)");
      return;
    }

    // Populate dropdown
    machineSelect.innerHTML = machines
      .map(
        m =>
          `<option value="${m.id}">${escapeHtml(m.machine_code)} &middot; ${escapeHtml(m.name)}</option>`
      )
      .join("");

    machineSelect.disabled = false;
    // Select first machine by default
    machineSelect.value = String(machines[0].id);
    updateMachineCard(machines[0]);

    setConnectionState("connected", "Control plane connected");
  } catch (error) {
    console.error("loadMachines failed:", error);
    machineSelect.innerHTML = `<option value="">Unable to connect to maintenance API</option>`;
    machineSelect.disabled = true;
    retryMachinesButton.classList.remove("hidden");
    updateMachineCard(null);
    setConnectionState("error", "Backend unavailable");
    showToast(error.message || "Backend unavailable. Please verify API connection.", true);
  }
}

/**
 * Append user query into conversation stream
 */
function addUserMessage(question) {
  const article = document.createElement("article");
  article.className = "message user";
  article.innerHTML = `
    <div class="message-label">Technician query</div>
    <div class="message-body">${escapeHtml(question)}</div>
  `;
  conversation.appendChild(article);
  conversation.scrollTop = conversation.scrollHeight;
}

/**
 * Create a live step loading placeholder in the conversation
 */
function createLoadingMessage() {
  const loading = document.createElement("article");
  loading.className = "message assistant-loading";
  loading.innerHTML = `
    <div class="message-label">Assistant &middot; Working</div>
    <div class="message-body loading-indicator">
      <div class="pulse-spinner" aria-hidden="true"></div>
      <span class="loading-step-text">Retrieving maintenance evidence...</span>
    </div>
  `;
  conversation.appendChild(loading);
  conversation.scrollTop = conversation.scrollHeight;

  const stepText = loading.querySelector(".loading-step-text");
  const stepTimer = setTimeout(() => {
    if (stepText) {
      stepText.textContent = "Analyzing machine context and synthesizing response...";
    }
  }, 2200);

  return {
    element: loading,
    cleanup: () => {
      clearTimeout(stepTimer);
      loading.remove();
    },
  };
}

/**
 * Render structured answer response
 */
function renderAnswer(payload) {
  const answer = payload.answer || {};
  const uncertain = Boolean(answer.insufficient_information);

  const listsData = [
    { title: "Possible Causes", items: answer.possible_causes },
    { title: "Recommended Actions", items: answer.recommended_actions },
    { title: "Safety Considerations", items: answer.safety_considerations },
  ];

  const sectionsHtml = listsData
    .filter(item => Array.isArray(item.items) && item.items.length > 0)
    .map(
      item => `
        <div class="answer-section">
          <div class="answer-title">${escapeHtml(item.title)}</div>
          <ul class="answer-list">${item.items.map(val => `<li>${escapeHtml(val)}</li>`).join("")}</ul>
        </div>
      `
    )
    .join("");

  const badgeText = uncertain ? "Insufficient Evidence" : "Grounded Guidance";
  const badgeClass = uncertain ? "badge-uncertain" : "";
  const cardTitle = uncertain ? "Evidence Limitation" : "Maintenance Assessment";

  const messageHtml = `
    <article class="message">
      <div class="message-label">Assistant &middot; ${badgeText}</div>
      <div class="message-body answer-card ${uncertain ? "uncertain" : ""}">
        <div class="answer-card-header">
          <div class="answer-title" style="margin-bottom:0">${cardTitle}</div>
          <span class="answer-badge ${badgeClass}">${badgeText}</span>
        </div>
        <p class="answer-text">${escapeHtml(answer.assessment || "No assessment was returned.")}</p>
        ${sectionsHtml}
      </div>
    </article>
  `;

  conversation.insertAdjacentHTML("beforeend", messageHtml);
  conversation.scrollTop = conversation.scrollHeight;
}

/**
 * Render evidence sources in the right rail
 */
function renderSources(sources = [], retrievalConfidence = null) {
  sourceCount.textContent = String(sources.length);

  if (retrievalConfidence !== null && retrievalConfidence !== undefined) {
    confidenceBanner.classList.remove("hidden");
    confidenceBanner.innerHTML = `Retrieval Confidence: <strong>${(retrievalConfidence * 100).toFixed(1)}%</strong>`;
  } else {
    confidenceBanner.classList.add("hidden");
    confidenceBanner.innerHTML = "";
  }

  if (!sources || sources.length === 0) {
    evidenceContent.innerHTML = `
      <div class="evidence-empty">
        <span class="empty-icon" aria-hidden="true">+</span>
        <p>No document sources were returned.</p>
      </div>
    `;
    return;
  }

  evidenceContent.innerHTML = sources
    .map((source, index) => {
      const title =
        source.document_name || source.source || source.document_id || "Verified evidence";

      const scoreText =
        source.score !== undefined && source.score !== null
          ? `Relevance: ${Number(source.score).toFixed(2)}`
          : null;

      const metaLines = [];
      if (source.section) {
        metaLines.push(`<div class="meta-row"><span class="meta-label">Section:</span> <span class="meta-val">${escapeHtml(source.section)}</span></div>`);
      }
      if (source.page !== undefined && source.page !== null) {
        metaLines.push(`<div class="meta-row"><span class="meta-label">Page:</span> <span class="meta-val">${escapeHtml(String(source.page))}</span></div>`);
      }
      if (source.chunk_id) {
        metaLines.push(`<div class="meta-row chunk-row"><span class="meta-label">Chunk:</span> <span class="meta-val chunk-val">${escapeHtml(String(source.chunk_id))}</span></div>`);
      }

      return `
        <div class="source-item">
          <div class="source-header">
            <div class="source-name">${String(index + 1).padStart(2, "0")} / ${escapeHtml(title)}</div>
            ${scoreText ? `<div class="source-score">${escapeHtml(scoreText)}</div>` : ""}
          </div>
          <div class="source-meta">
            ${metaLines.length > 0 ? metaLines.join("") : "Metadata unavailable"}
          </div>
        </div>
      `;
    })
    .join("");
}

/**
 * Extract human-readable error messages based on HTTP status
 */
function parseErrorMessage(response, payload) {
  if (response.status === 404) {
    return "The requested machine could not be found in the register.";
  }
  if (response.status === 422) {
    return "Please select a valid machine and enter a maintenance question.";
  }
  if (response.status === 502 || response.status === 503) {
    return "The maintenance assistant is temporarily unavailable.";
  }
  if (payload && payload.detail) {
    if (typeof payload.detail === "string") return payload.detail;
    if (payload.detail.message) return payload.detail.message;
  }
  return "Backend unavailable. Please verify the API connection and try again.";
}

/**
 * Submit chat question handler
 */
async function submitQuestion(event) {
  if (event) event.preventDefault();

  const question = questionInput.value.trim();
  const machineId = Number(machineSelect.value);

  if (!machineId) {
    showToast("Please select a machine first.", true);
    return;
  }
  if (!question) {
    showToast("Please enter a maintenance question.", true);
    questionInput.focus();
    return;
  }

  if (isSubmitting) return;
  isSubmitting = true;

  // Post user query to UI
  addUserMessage(question);
  questionInput.value = "";
  validateForm();

  // Loading state in composer & chat
  sendButton.querySelector(".btn-text").textContent = "Working...";
  inputHint.textContent = "Retrieving maintenance evidence...";
  const loader = createLoadingMessage();

  try {
    const response = await apiFetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        machine_id: machineId,
        question: question,
        top_k: 5,
      }),
    });

    const payload = await response.json().catch(() => ({}));
    loader.cleanup();

    if (!response.ok) {
      throw new Error(parseErrorMessage(response, payload));
    }

    renderAnswer(payload);
    renderSources(payload.sources || [], payload.retrieval_confidence);
    setConnectionState("connected", "Control plane connected");
  } catch (error) {
    console.error("submitQuestion error:", error);
    loader.cleanup();

    const errorMsg = error.message || "Backend unavailable. Please try again.";
    showToast(errorMsg, true);

    const errorArticle = document.createElement("article");
    errorArticle.className = "message";
    errorArticle.innerHTML = `
      <div class="message-label">Assistant &middot; Error</div>
      <div class="message-body answer-card error-card">
        <div class="answer-title" style="color:var(--crimson)">Request Failed</div>
        <p class="answer-text">${escapeHtml(errorMsg)}</p>
      </div>
    `;
    conversation.appendChild(errorArticle);
    conversation.scrollTop = conversation.scrollHeight;

    setConnectionState("error", "Assistant connection issue");
  } finally {
    isSubmitting = false;
    sendButton.querySelector(".btn-text").textContent = "Ask assistant";
    validateForm();
  }
}

/**
 * Reset application conversation and reload machines
 */
function resetApplication() {
  conversation.innerHTML = `
    <div class="welcome-message">
      <span class="welcome-index">01</span>
      <div>
        <h3>What needs attention?</h3>
        <p>
          Ask about sensor readings, elevated vibration, troubleshooting procedures, or suspected component wear. Select an active machine first so responses incorporate operational parameters.
        </p>
      </div>
    </div>
  `;
  renderSources([], null);
  questionInput.value = "";
  loadMachines();
}

// Event Listeners
machineSelect.addEventListener("change", () => {
  const chosen = machines.find(m => String(m.id) === String(machineSelect.value));
  updateMachineCard(chosen);
});

retryMachinesButton.addEventListener("click", () => {
  loadMachines();
});

questionInput.addEventListener("input", validateForm);

questionInput.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    if (!sendButton.disabled && !isSubmitting) {
      chatForm.requestSubmit();
    }
  }
});

chatForm.addEventListener("submit", submitQuestion);

clearButton.addEventListener("click", () => {
  conversation.innerHTML = `
    <div class="welcome-message">
      <span class="welcome-index">01</span>
      <div>
        <h3>What needs attention?</h3>
        <p>
          Ask about sensor readings, elevated vibration, troubleshooting procedures, or suspected component wear. Select an active machine first so responses incorporate operational parameters.
        </p>
      </div>
    </div>
  `;
  renderSources([], null);
});

globalRefreshButton.addEventListener("click", resetApplication);

// Initial Load
loadMachines();
