const API_BASE = "/api";

interface Article {
  id: string;
  source: string;
  title: string;
  authors: { name: string }[] | string; // Zotero returns string sometimes
  journal: string;
  pub_date: string;
  doi: string | null;
  url: string;
  pdf_url?: string;
  snippet?: string;
  llm_relevance_score?: number;
  llm_relevance_reason?: string;
}

interface SearchResponse {
  query: string;
  total: number;
  original_total?: number;
  llm_filtered?: boolean;
  errors: { error: string; message: string }[];
  articles: Article[];
}

// DOM Elements
const form = document.getElementById("search-form") as HTMLFormElement;
const queryInput = document.getElementById("query") as HTMLInputElement;
const submitBtn = document.getElementById("submit-btn") as HTMLButtonElement;
const statusEl = document.getElementById("status") as HTMLDivElement;
const resultsEl = document.getElementById("results") as HTMLElement;

// Views
const searchView = document.getElementById("search-view") as HTMLElement;
const libraryView = document.getElementById("library-view") as HTMLElement;
const libraryResultsEl = document.getElementById(
  "library-results",
) as HTMLElement;

// Nav
const savedRefsBtn = document.getElementById(
  "saved-refs-btn",
) as HTMLButtonElement;
const backToSearchBtn = document.getElementById(
  "back-to-search-btn",
) as HTMLButtonElement;
const saveAllBtn = document.getElementById("save-all-btn") as HTMLButtonElement;
const resultsControls = document.getElementById(
  "results-controls",
) as HTMLDivElement;

let currentArticles: Article[] = []; // Store current search results to save them

function setStatus(
  message: string,
  type: "idle" | "loading" | "success" | "error" = "idle",
) {
  statusEl.textContent = message;
  statusEl.className = "status " + type;
}

function showToast(
  title: string,
  message: string,
  type: "success" | "error" | "info" = "info",
  duration: number = 8000,
) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  toast.innerHTML = `
        <div class="toast-header">
            <span>${escapeHtml(title)}</span>
            <button class="toast-close">&times;</button>
        </div>
        <div class="toast-body">${escapeHtml(message)}</div>
    `;

  container.appendChild(toast);

  // Close logic
  const closeBtn = toast.querySelector(".toast-close");
  closeBtn?.addEventListener("click", () => {
    toast.style.animation = "fadeOut 0.3s ease-out forwards";
    setTimeout(() => toast.remove(), 300);
  });

  // Auto dismiss
  if (duration > 0) {
    setTimeout(() => {
      if (document.body.contains(toast)) {
        toast.style.animation = "fadeOut 0.3s ease-out forwards";
        setTimeout(() => toast.remove(), 300);
      }
    }, duration);
  }
}

function sourceBadgeClass(source: string): string {
  if (source === "arxiv") return "arxiv";
  if (source === "semantic_scholar") return "semantic_scholar";
  if (source === "openalex") return "openalex";
  if (source === "crossref") return "crossref";
  if (source === "scopus") return "scopus";
  if (source === "springer") return "springer";
  if (source === "zotero") return "zotero";
  return "";
}

function sourceLabel(source: string): string {
  if (source === "semantic_scholar") return "Semantic Scholar";
  if (source === "openalex") return "OpenAlex";
  if (source === "crossref") return "CrossRef";
  if (source === "scopus") return "Scopus";
  if (source === "springer") return "Springer Link";
  if (source === "zotero") return "Zotero Library";
  return source.charAt(0).toUpperCase() + source.slice(1);
}

function renderArticle(
  a: Article,
  index: number,
  isSavedView: boolean = false,
): string {
  let authorsStr = "";
  if (typeof a.authors === "string") {
    authorsStr = a.authors;
  } else if (Array.isArray(a.authors)) {
    authorsStr = a.authors.map((x) => x.name).join(", ");
  }

  const meta = [authorsStr, a.journal, a.pub_date].filter(Boolean).join(" · ");
  const links = [
    `<a href="${a.url}" target="_blank" rel="noopener">Ver artículo</a>`,
  ];
  if (a.pdf_url) {
    links.push(`<a href="${a.pdf_url}" target="_blank" rel="noopener">PDF</a>`);
  }
  if (a.doi) {
    links.push(
      `<a href="https://doi.org/${a.doi}" target="_blank" rel="noopener">DOI</a>`,
    );
  }

  // LLM relevance badge
  let llmBadge = "";
  if (a.llm_relevance_score !== undefined) {
    const scorePercent = Math.round(a.llm_relevance_score * 100);
    const scoreClass =
      scorePercent >= 90
        ? "score-high"
        : scorePercent >= 70
          ? "score-medium"
          : "score-low";
    llmBadge = `
            <div class="llm-relevance ${scoreClass}">
                <span class="llm-score">🤖 ${scorePercent}% relevante</span>
                ${a.llm_relevance_reason ? `<span class="llm-reason">${escapeHtml(a.llm_relevance_reason)}</span>` : ""}
            </div>
        `;
  }

  // Save button (only for search results)
  let saveBtn = "";
  if (!isSavedView) {
    saveBtn = `<button class="save-btn" onclick="window.saveToZotero(${index})">💾 Guardar</button>`;
  }

  return `
    <article class="article-card" data-source="${a.source}">
      <h3><a href="${a.url}" target="_blank" rel="noopener">${escapeHtml(a.title)}</a></h3>
      <div class="article-meta">
        <span class="source-badge ${sourceBadgeClass(a.source)}">${sourceLabel(a.source)}</span>
        ${meta ? `<span>${escapeHtml(meta)}</span>` : ""}
      </div>
      ${llmBadge}
      ${a.snippet ? `<p class="snippet">${escapeHtml(a.snippet)}</p>` : ""}
      <div class="links">
        ${links.join("")}
        ${saveBtn}
      </div>
    </article>
  `;
}

function escapeHtml(s: string): string {
  if (!s) return "";
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

// Expose functionality to global scope for inline onclick
(window as any).saveToZotero = async (index: number) => {
  const article = currentArticles[index];
  if (!article) return;

  // Find button within the specific article card in resultsEl
  // Robust way: get all save buttons in results
  const btns = resultsEl.querySelectorAll(".save-btn");
  const btn = btns[index] as HTMLButtonElement;

  if (!btn) return;

  const originalText = btn.textContent;
  btn.textContent = "Guardando...";
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/zotero/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(article),
    });
    const data = await res.json();

    if (res.ok && data.success) {
      btn.textContent = "✅ Guardado";
      btn.classList.add("success");
      // Optional: reset after 2s
      setTimeout(() => {
        btn.textContent = "💾 Guardado";
      }, 2000);
    } else {
      alert(data.error || "Error al guardar");
      btn.textContent = originalText;
      btn.disabled = false;
    }
  } catch (e) {
    alert("Error de conexión al guardar.");
    btn.textContent = originalText;
    btn.disabled = false;
  }
};

function showSearch() {
  libraryView.classList.add("hidden");
  searchView.classList.remove("hidden");
  // Determine if we should restore results
  if (currentArticles.length > 0) {
    resultsEl.innerHTML = currentArticles
      .map((a, i) => renderArticle(a, i, false))
      .join("");
    setStatus(
      `Resultados anteriores restaurados (${currentArticles.length})`,
      "success",
    );
  } else {
    setStatus("Listo para buscar", "idle");
  }
  updateControlsVisibility();
}

async function loadSavedReferences() {
  searchView.classList.add("hidden");
  resultsControls.classList.add("hidden"); // Hide button in library view
  libraryView.classList.remove("hidden");

  libraryResultsEl.innerHTML =
    "<p class='status loading'>Cargando biblioteca...</p>";

  try {
    const res = await fetch(`${API_BASE}/zotero/items`);
    if (!res.ok) throw new Error("Error al obtener referencias");
    const items: Article[] = await res.json();

    if (items.length === 0) {
      libraryResultsEl.innerHTML =
        "<p class='status'>No tienes referencias guardadas aún.</p>";
      return;
    }

    libraryResultsEl.innerHTML = items
      .map((a, i) => renderArticle(a, i, true))
      .join("");
  } catch (e) {
    libraryResultsEl.innerHTML =
      "<p class='status error'>Error al cargar biblioteca Zotero. Verifica tu configuración.</p>";
  }
}

function updateControlsVisibility() {
  if (currentArticles.length > 0 && !searchView.classList.contains("hidden")) {
    resultsControls.classList.remove("hidden");
  } else {
    resultsControls.classList.add("hidden");
  }
}

// Event Listeners
savedRefsBtn.addEventListener("click", loadSavedReferences);
backToSearchBtn.addEventListener("click", showSearch);

saveAllBtn.addEventListener("click", async () => {
  if (currentArticles.length === 0) return;

  const originalText = saveAllBtn.textContent;
  saveAllBtn.textContent = "⏳ Guardando todo... (esto puede tardar)";
  saveAllBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/zotero/items/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentArticles),
    });
    const data = await res.json();

    if (data.saved !== undefined) {
      const msg = `✅ Guardados: ${data.saved}\n⏭️ Omitidos: ${data.skipped}\n${data.errors.length ? "⚠️ Errores: " + data.errors.length : ""}`;
      showToast("Proceso Finalizado", msg, "success", 7000);
    } else {
      showToast("Error", "Error en la respuesta del servidor", "error");
    }
  } catch (e) {
    showToast("Error", "Error de conexión al guardar lote.", "error");
  } finally {
    saveAllBtn.textContent = originalText;
    saveAllBtn.disabled = false;
  }
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = queryInput.value.trim();
  if (!q) return;

  const sources = Array.from(
    form.querySelectorAll<HTMLInputElement>('input[name="source"]:checked'),
  )
    .map((c) => c.value)
    .join(",");
  if (!sources) {
    setStatus("Selecciona al menos una fuente.", "error");
    return;
  }

  const params = new URLSearchParams({
    q,
    sources,
    max_results: (document.getElementById("max_results") as HTMLInputElement)
      .value,
    sort: (document.getElementById("sort") as HTMLSelectElement).value,
  });
  const fromDate = (document.getElementById("from_date") as HTMLInputElement)
    .value;
  const toDate = (document.getElementById("to_date") as HTMLInputElement).value;
  const useLLMFilter = (
    document.getElementById("use_llm_filter") as HTMLInputElement
  ).checked;
  const aiContext = (
    document.getElementById("ai-context") as HTMLTextAreaElement
  ).value.trim();

  if (fromDate) params.set("from_date", fromDate);
  if (toDate) params.set("to_date", toDate);
  if (useLLMFilter) {
    params.set("use_llm_filter", "true");
    if (aiContext) params.set("context", aiContext);
  }

  setStatus("Buscando...", "loading");
  submitBtn.disabled = true;
  resultsEl.innerHTML = "";
  currentArticles = []; // Reset current articles

  try {
    const res = await fetch(`${API_BASE}/search?${params}`);
    if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
    const data: SearchResponse = await res.json();

    let statusMsg = `Encontrados ${data.total} artículos`;
    if (data.llm_filtered) {
      statusMsg += " (Filtrado por IA";
      if (data.original_total && data.original_total > data.total) {
        statusMsg += `, de ${data.original_total} originales`;
      }
      statusMsg += ")";
    }
    if (data.errors?.length) {
      statusMsg += `. Algunas fuentes fallaron: ${data.errors.map((e) => e.error).join(", ")}`;
    }
    setStatus(statusMsg, "success");

    currentArticles = data.articles || [];
    updateControlsVisibility(); // Show button if results exist

    if (currentArticles.length) {
      resultsEl.innerHTML = currentArticles
        .map((a, index) => renderArticle(a, index, false))
        .join("");
    } else {
      resultsEl.innerHTML = `
        <p class="status text-muted">No se encontraron artículos para "${escapeHtml(q)}". Prueba otros términos o fuentes.</p>
      `;
    }
  } catch (err) {
    setStatus(
      "Error al buscar. ¿Está corriendo el backend? (python -m uvicorn app.main:app --reload)",
      "error",
    );
    resultsEl.innerHTML = "";
  } finally {
    submitBtn.disabled = false;
  }
});
