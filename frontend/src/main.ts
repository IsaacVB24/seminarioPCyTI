const API_BASE = "/api";

interface Article {
  id: string;
  source: string;
  title: string;
  authors: { name: string }[];
  journal: string;
  pub_date: string;
  doi: string | null;
  url: string;
  pdf_url?: string;
  snippet: string;
}

interface SearchResponse {
  query: string;
  total: number;
  errors: { error: string; message: string }[];
  articles: Article[];
}

const form = document.getElementById("search-form") as HTMLFormElement;
const queryInput = document.getElementById("query") as HTMLInputElement;
const submitBtn = document.getElementById("submit-btn") as HTMLButtonElement;
const statusEl = document.getElementById("status") as HTMLDivElement;
const resultsEl = document.getElementById("results") as HTMLElement;

function setStatus(message: string, type: "idle" | "loading" | "success" | "error" = "idle") {
  statusEl.textContent = message;
  statusEl.className = "status " + type;
}

function sourceBadgeClass(source: string): string {
  if (source === "pubmed") return "pubmed";
  if (source === "arxiv") return "arxiv";
  if (source === "semantic_scholar") return "semantic_scholar";
  return "";
}

function sourceLabel(source: string): string {
  if (source === "semantic_scholar") return "Semantic Scholar";
  return source.charAt(0).toUpperCase() + source.slice(1);
}

function renderArticle(a: Article): string {
  const authorsStr = a.authors?.length
    ? a.authors.map((x) => x.name).join(", ")
    : "";
  const meta = [authorsStr, a.journal, a.pub_date].filter(Boolean).join(" · ");
  const links = [
    `<a href="${a.url}" target="_blank" rel="noopener">Ver artículo</a>`,
  ];
  if (a.pdf_url) {
    links.push(`<a href="${a.pdf_url}" target="_blank" rel="noopener">PDF</a>`);
  }
  if (a.doi) {
    links.push(
      `<a href="https://doi.org/${a.doi}" target="_blank" rel="noopener">DOI</a>`
    );
  }
  return `
    <article class="article-card" data-source="${a.source}">
      <h3><a href="${a.url}" target="_blank" rel="noopener">${escapeHtml(a.title)}</a></h3>
      <div class="article-meta">
        <span class="source-badge ${sourceBadgeClass(a.source)}">${sourceLabel(a.source)}</span>
        ${meta ? `<span>${escapeHtml(meta)}</span>` : ""}
      </div>
      ${a.snippet ? `<p class="snippet">${escapeHtml(a.snippet)}</p>` : ""}
      <div class="links">${links.join("")}</div>
    </article>
  `;
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = queryInput.value.trim();
  if (!q) return;

  const sources = Array.from(
    form.querySelectorAll<HTMLInputElement>('input[name="source"]:checked')
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
    max_results: (document.getElementById("max_results") as HTMLInputElement).value,
    sort: (document.getElementById("sort") as HTMLSelectElement).value,
  });
  const fromDate = (document.getElementById("from_date") as HTMLInputElement).value;
  const toDate = (document.getElementById("to_date") as HTMLInputElement).value;
  if (fromDate) params.set("from_date", fromDate);
  if (toDate) params.set("to_date", toDate);

  setStatus("Buscando...", "loading");
  submitBtn.disabled = true;
  resultsEl.innerHTML = "";

  try {
    const res = await fetch(`${API_BASE}/search?${params}`);
    if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
    const data: SearchResponse = await res.json();

    if (data.errors?.length) {
      setStatus(
        `Encontrados ${data.total} artículos. Algunas fuentes fallaron: ${data.errors.map((e) => e.error).join(", ")}`,
        "success"
      );
    } else {
      setStatus(`Encontrados ${data.total} artículos.`, "success");
    }

    if (data.articles?.length) {
      resultsEl.innerHTML = data.articles.map(renderArticle).join("");
    } else {
      resultsEl.innerHTML = `
        <p class="status text-muted">No se encontraron artículos para "${escapeHtml(q)}". Prueba otros términos o fuentes.</p>
      `;
    }
  } catch (err) {
    setStatus(
      "Error al buscar. ¿Está corriendo el backend? (python -m uvicorn app.main:app --reload)",
      "error"
    );
    resultsEl.innerHTML = "";
  } finally {
    submitBtn.disabled = false;
  }
});
