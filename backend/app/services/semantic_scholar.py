"""Búsqueda en Semantic Scholar (multidisciplinario)."""
import httpx
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

BASE = "https://api.semanticscholar.org/graph/v1"


async def search_semantic_scholar(
    query: str,
    max_results: int = 20,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict]:
    """Busca en Semantic Scholar. Fechas en YYYY-MM-DD."""
    logger.info(f"[SEMANTIC_SCHOLAR] Searching for: '{query}' (max_results={max_results})")
    
    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": "paperId,title,authors,year,venue,abstract,externalIds,url",
    }
    if from_date:
        params["year"] = from_date[:4]
    # Semantic Scholar no tiene filtro to_date fino en la búsqueda

    headers = {"User-Agent": "SeminarioResearch/1.0"}

    # Retry logic for rate limiting (429 errors)
    max_retries = 3
    for attempt in range(max_retries):
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            url = f"{BASE}/paper/search"
            logger.debug(f"[SEMANTIC_SCHOLAR] GET {url} (attempt {attempt + 1})")
            r = await client.get(url, params=params)
            logger.info(f"[SEMANTIC_SCHOLAR] Response status: {r.status_code}")
            if r.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"[SEMANTIC_SCHOLAR] Rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
            r.raise_for_status()
            data = r.json()
            break
    else:
        # All retries exhausted
        logger.error("[SEMANTIC_SCHOLAR] All retries exhausted")
        return []

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
    
    logger.info(f"[SEMANTIC_SCHOLAR] Found {len(articles)} articles")
    return articles
