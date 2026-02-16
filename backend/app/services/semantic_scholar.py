"""Búsqueda en Semantic Scholar (multidisciplinario)."""
import logging
import urllib.request
import urllib.parse
import json
import time
from typing import Optional

logger = logging.getLogger(__name__)

BASE = "https://api.semanticscholar.org/graph/v1"


async def search_semantic_scholar(
    query: str,
    max_results: int = 20,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict]:
    """Busca en Semantic Scholar using urllib."""
    logger.info(f"[SEMANTIC_SCHOLAR] Searching for: '{query}' (max_results={max_results})")
    
    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": "paperId,title,authors,year,venue,abstract,externalIds,url",
    }
    if from_date:
        params["year"] = from_date[:4]

    headers = {"User-Agent": "SeminarioResearch/1.0"}
    query_string = urllib.parse.urlencode(params)
    url = f"{BASE}/paper/search?{query_string}"

    max_retries = 3
    data = {}
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                logger.info(f"[SEMANTIC_SCHOLAR] Response status: {response.getcode()}")
                if response.getcode() == 200:
                    body = response.read().decode('utf-8')
                    data = json.loads(body)
                    break
                elif response.getcode() == 429:
                     wait_time = 2 ** attempt
                     logger.warning(f"[SEMANTIC_SCHOLAR] Rate limited, waiting {wait_time}s...")
                     time.sleep(wait_time) # Blocking sleep is acceptable here for simplicity in async wrapper context or use asyncio.sleep if needed but urllib is blocking anyway
                     continue
                else:
                    logger.error(f"[SEMANTIC_SCHOLAR] Error {response.getcode()}")
                    return [{"error": "semantic_scholar", "message": f"Error API: {response.getcode()}"}]
                    
        except urllib.request.HTTPError as e:
            if e.code == 429:
                 if attempt < max_retries - 1:
                     wait_time = 2 ** attempt
                     logger.warning(f"[SEMANTIC_SCHOLAR] Rate limited (HTTPError), waiting {wait_time}s...")
                     time.sleep(wait_time)
                     continue
            logger.error(f"[SEMANTIC_SCHOLAR] HTTP Error: {e.code}")
            return [{"error": "semantic_scholar", "message": f"Error HTTP: {e.code}"}]
        except Exception as e:
            logger.error(f"[SEMANTIC_SCHOLAR] Connection error: {e}")
            return [{"error": "semantic_scholar", "message": f"Error de conexión: {str(e)}"}]
    else:
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
