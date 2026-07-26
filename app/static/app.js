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
  invalidateCache: document.querySelector("#invalidate-cache"),
};

let defaults = { top_k: 2, relevance_threshold: 0.35 };
let apiKey = "";

function authenticatedHeaders(includeJson = false) {
  const headers = { "X-API-Key": apiKey };
  if (includeJson) headers["Content-Type"] = "application/json";
  return headers;
}

async function readJsonResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  if (response.status === 504) {
    throw new Error(
      "The local model took too long to answer. Please retry; the completed answer may now be cached.",
    );
  }

  if (response.status === 502 || response.status === 503) {
    throw new Error(
      "The model service is temporarily unavailable. Please try again shortly.",
    );
  }

  throw new Error(
    `The server returned an unexpected response (${response.status}).`,
  );
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

function normalizeQuestion(value) {
  return value.toLowerCase().trim().replace(/\s+/g, " ");
}

function markSuggestionCached(question, wasHit) {
  const normalizedQuestion = normalizeQuestion(question);
  const button = [...document.querySelectorAll("[data-question]")]
    .find((item) => normalizeQuestion(item.dataset.question) === normalizedQuestion);
  if (!button) return;

  button.classList.add("cached");
  let state = button.querySelector(".suggestion-cache-state");
  if (!state) {
    state = document.createElement("span");
    state.className = "suggestion-cache-state";
    button.append(state);
  }
  state.textContent = wasHit ? "Cache hit" : "Cached";
  button.title = wasHit
    ? "This answer was reused from the server cache."
    : "This answer is now stored for the next identical request.";
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
    const config = await readJsonResponse(response);
    defaults = config.defaults;
    resetControls();
    setText("provider", config.provider);
    setText("llm-model", config.llm_model);
    setText("embedding-model", config.embedding_model);
    setText("document-count", config.document_count);
    setText("cache-ttl", `${config.cache.ttl_seconds}s`);
    setText("cache-capacity", `${config.cache.max_entries} entries`);
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

  const cacheBadge = fragment.querySelector(".cache-badge");
  cacheBadge.textContent = data.cache.hit
    ? "Cache hit · reused"
    : data.cache.expires_at
      ? "Cache miss · stored"
      : "Not cached";
  if (data.cache.hit) cacheBadge.classList.add("hit");

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
  setText("cache-status", data.cache.hit ? "Hit · reused" : "Miss · stored");
  setText(
    "cache-expires",
    data.cache.expires_at
      ? new Date(data.cache.expires_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
      : "Not cached",
  );
  setText("run-grounding", data.grounded ? "Grounded answer" : "Fallback");
  if (data.cache.expires_at) {
    markSuggestionCached(question, data.cache.hit);
  }
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
    const data = await readJsonResponse(response);
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
els.invalidateCache.addEventListener("click", async () => {
  if (!apiKey) {
    setText("cache-status", "API key required");
    return;
  }
  try {
    const response = await fetch("/api/v1/cache", {
      method: "DELETE",
      headers: authenticatedHeaders(),
    });
    if (!response.ok) throw new Error();
    const data = await readJsonResponse(response);
    setText("cache-status", `Invalidated · ${data.invalidated_entries}`);
    setText("cache-expires", "—");
    document.querySelectorAll("[data-question].cached").forEach((button) => {
      button.classList.remove("cached");
      button.removeAttribute("title");
      button.querySelector(".suggestion-cache-state")?.remove();
    });
  } catch {
    setText("cache-status", "Invalidation failed");
  }
});

syncControls();
loadHealth();
