const els = {
  form: document.querySelector("#question-form"),
  question: document.querySelector("#question"),
  conversation: document.querySelector("#conversation"),
  empty: document.querySelector("#empty-state"),
  template: document.querySelector("#answer-template"),
  status: document.querySelector("#api-status"),
  topK: document.querySelector("#top-k"),
  topKValue: document.querySelector("#top-k-value"),
  threshold: document.querySelector("#threshold"),
  thresholdValue: document.querySelector("#threshold-value"),
  reset: document.querySelector("#reset-controls"),
  apiKey: document.querySelector("#api-key"),
  applyKey: document.querySelector("#apply-key"),
};

let defaults = { top_k: 2, relevance_threshold: 0.35 };
let apiKey = "";

function authenticatedHeaders(includeJson = false) {
  const headers = { "X-API-Key": apiKey };
  if (includeJson) headers["Content-Type"] = "application/json";
  return headers;
}

function setText(id, value) {
  document.querySelector(`#${id}`).textContent = value;
}

function syncControls() {
  els.topKValue.textContent = `${els.topK.value} ${els.topK.value === "1" ? "chunk" : "chunks"}`;
  els.thresholdValue.textContent = Number(els.threshold.value).toFixed(2);
}

function resetControls() {
  els.topK.value = defaults.top_k;
  els.threshold.value = defaults.relevance_threshold;
  syncControls();
}

async function loadHealth() {
  try {
    const response = await fetch("/api/v1/health");
    if (!response.ok) throw new Error();
    els.status.classList.add("online");
    els.status.querySelector("span:last-child").textContent = "API connected · key required";
  } catch {
    els.status.classList.add("offline");
    els.status.querySelector("span:last-child").textContent = "API unavailable";
  }
}

async function loadConfig() {
  try {
    const response = await fetch("/api/v1/config", {
      headers: authenticatedHeaders(),
    });
    if (!response.ok) throw new Error("Invalid API key");
    const config = await response.json();
    defaults = config.defaults;
    resetControls();
    setText("provider", config.provider);
    setText("llm-model", config.llm_model);
    setText("embedding-model", config.embedding_model);
    setText("document-count", config.document_count);
    setText("key-status", "Connected");
    els.apiKey.value = "";
    els.status.querySelector("span:last-child").textContent = "API connected · authorized";
  } catch {
    apiKey = "";
    setText("key-status", "Rejected");
    els.status.querySelector("span:last-child").textContent = "API connected · key required";
  }
}

function renderAnswer(question, data) {
  els.empty?.remove();
  const fragment = els.template.content.cloneNode(true);
  fragment.querySelector(".question-row p").textContent = question;
  fragment.querySelector(".answer-copy").textContent = data.answer;

  const badge = fragment.querySelector(".grounded-badge");
  badge.textContent = data.grounded ? "Grounded" : "Fallback";
  if (!data.grounded) badge.classList.add("ungrounded");

  const sourceList = fragment.querySelector(".source-list");
  data.sources.forEach((source) => {
    const card = document.createElement("div");
    card.className = "source-card";
    const title = document.createElement("strong");
    title.textContent = source.title;
    const origin = document.createElement("small");
    origin.textContent = `${source.id} · ${source.source}`;
    const score = document.createElement("span");
    score.className = "score";
    score.textContent = source.score.toFixed(4);
    card.append(title, origin, score);
    sourceList.append(card);
  });

  els.conversation.replaceChildren(fragment);
  setText("request-id", data.request_id);
  setText("sources-used", data.sources.length);
  setText("applied-top-k", data.parameters.top_k);
  setText("applied-threshold", data.parameters.relevance_threshold.toFixed(2));
  setText("security-status", data.security.blocked ? "Blocked" : "Passed");
  setText("security-reason", data.security.reason || "—");
  setText("run-grounding", data.grounded ? "Grounded answer" : "Fallback");
}

function renderError(message) {
  const error = document.createElement("div");
  error.className = "error-message";
  error.textContent = message;
  els.empty?.remove();
  els.conversation.replaceChildren(error);
}

async function ask(question) {
  els.form.classList.add("loading");
  els.form.querySelector("button").disabled = true;
  try {
    const response = await fetch("/api/v1/answer", {
      method: "POST",
      headers: authenticatedHeaders(true),
      body: JSON.stringify({
        question,
        top_k: Number(els.topK.value),
        relevance_threshold: Number(els.threshold.value),
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = data?.error?.message || data?.detail?.[0]?.msg || "The request could not be completed.";
      throw new Error(detail);
    }
    renderAnswer(question, data);
    els.question.value = "";
    els.question.style.height = "auto";
  } catch (error) {
    renderError(error.message);
  } finally {
    els.form.classList.remove("loading");
    els.form.querySelector("button").disabled = false;
    els.question.focus();
  }
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = els.question.value.trim();
  if (question.length >= 3) ask(question);
});

els.question.addEventListener("input", () => {
  els.question.style.height = "auto";
  els.question.style.height = `${els.question.scrollHeight}px`;
});

els.question.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    els.form.requestSubmit();
  }
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    els.question.value = button.dataset.question;
    els.form.requestSubmit();
  });
});

els.topK.addEventListener("input", syncControls);
els.threshold.addEventListener("input", syncControls);
els.reset.addEventListener("click", resetControls);
els.applyKey.addEventListener("click", () => {
  apiKey = els.apiKey.value;
  loadConfig();
});
els.apiKey.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    els.applyKey.click();
  }
});

syncControls();
loadHealth();
