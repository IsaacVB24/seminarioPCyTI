"""Búsqueda en OpenAlex."""
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org/works"

async def search_openalex(
    query: str,
    max_results: int = 20,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict]:
    """
    Busca en OpenAlex.
    Documentación: https://docs.openalex.org/api-entities/works/search-works
    """
    logger.info(f"[OPENALEX] Searching for: '{query}' (max_results={max_results})")
    
    # OpenAlex usa 'search' param para búsqueda de texto completo
    # y 'filter' para filtros estructurados (como fechas)
    params = {
        "search": query,
        "per-page": min(max_results, 100),
        "mailto": "" # Good practice to include email
    }

    # Construir filtros
    filters = []
    
    # Filtro de años si se proporcionan fechas
    # OpenAlex usa 'from_publication_date' y 'to_publication_date' en el filtro
    if from_date:
        filters.append(f"from_publication_date:{from_date}")
    if to_date:
        filters.append(f"to_publication_date:{to_date}")
        
    if filters:
        params["filter"] = ",".join(filters)

    headers = {
        "User-Agent": "SeminarioResearch/1.0 (mailto:researcher@seminariopcyt.edu.mx)"
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        logger.debug(f"[OPENALEX] GET {BASE_URL} params={params}")
        r = await client.get(BASE_URL, params=params)
        logger.info(f"[OPENALEX] Response status: {r.status_code}")
        
        if r.status_code != 200:
            logger.error(f"[OPENALEX] Error: {r.text}")
            r.raise_for_status()
            
        data = r.json()

    results = data.get("results", [])
    articles = []

    for item in results:
        # Extraer ID corto (W123456789)
        oa_id = item.get("id", "")
        short_id = oa_id.split("/")[-1] if oa_id else ""
        
        # Título
        title = item.get("display_name") or item.get("title") or "Sin título"
        
        # Autores
        authorships = item.get("authorships", [])
        authors = []
        for auth in authorships:
            author_obj = auth.get("author", {})
            name = author_obj.get("display_name", "")
            if name:
                authors.append({"name": name})
        
        # Journal / Venue
        primary_loc = item.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        journal = source.get("display_name") or "OpenAlex"
        
        # Fecha
        pub_date = item.get("publication_date", "") or str(item.get("publication_year", ""))
        
        # URL / DOI
        doi = item.get("doi")
        url = doi or oa_id # Prefer DOI as URL, fallback to OpenAlex ID URL
        
        snippet = title
        
        articles.append({
            "id": short_id,
            "source": "openalex",
            "title": title,
            "authors": authors,
            "journal": journal,
            "pub_date": pub_date,
            "doi": doi,
            "url": url,
            "snippet": snippet,
        })

    logger.info(f"[OPENALEX] Found {len(articles)} articles")
    return articles
