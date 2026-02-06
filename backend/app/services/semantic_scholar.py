"""Búsqueda en Semantic Scholar (multidisciplinario)."""
import httpx
from typing import Optional

BASE = "https://api.semanticscholar.org/graph/v1"


async def search_semantic_scholar(
    query: str,
    max_results: int = 20,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict]:
    """Busca en Semantic Scholar. Fechas en YYYY-MM-DD."""
    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": "paperId,title,authors,year,venue,abstract,externalIds,url",
    }
    if from_date:
        params["year"] = from_date[:4]
    # Semantic Scholar no tiene filtro to_date fino en la búsqueda

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{BASE}/paper/search", params=params)
        r.raise_for_status()
        data = r.json()

    hits = data.get("data", [])
    articles = []
    for hit in hits:
        ext = hit.get("externalIds") or {}
        authors = [{"name": a.get("name", "")} for a in (hit.get("authors") or [])]
        year = hit.get("year")
        pub_date = str(year) if year else ""
        if to_date and year and str(year) > to_date[:4]:
            continue
        if from_date and year and str(year) < from_date[:4]:
            continue

        articles.append({
            "id": hit.get("paperId", ""),
            "source": "semantic_scholar",
            "title": hit.get("title", ""),
            "authors": authors,
            "journal": hit.get("venue", "") or "Semantic Scholar",
            "pub_date": pub_date,
            "doi": ext.get("DOI"),
            "url": hit.get("url", f"https://www.semanticscholar.org/paper/{hit.get('paperId', '')}"),
            "snippet": (hit.get("abstract") or "")[:300] or hit.get("title", ""),
        })
    return articles
