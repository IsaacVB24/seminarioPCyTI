"""Búsqueda en CrossRef."""
import httpx
import logging
from typing import Optional
import urllib.parse

logger = logging.getLogger(__name__)

BASE_URL = "https://api.crossref.org/works"

async def search_crossref(
    query: str,
    max_results: int = 20,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict]:
    """
    Busca en CrossRef.
    """
    logger.info(f"[CROSSREF] Searching for: '{query}' (max_results={max_results})")
    
    params = {
        "query": query,
        "rows": min(max_results, 100),
        "mailto": "researcher@seminariopcyt.edu.mx" 
    }

    filters = []
    
    if from_date:
        filters.append(f"from-pub-date:{from_date}")
    if to_date:
        filters.append(f"until-pub-date:{to_date}")
        
    if filters:
        params["filter"] = ",".join(filters)

    headers = {
        "User-Agent": "SeminarioResearch/1.0 (mailto:researcher@seminariopcyt.edu.mx)"
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        # CrossRef requiere codificación correcta de parámetros
        # httpx lo maneja, pero a veces con caracteres especiales en filtros hay que tener cuidado.
        logger.debug(f"[CROSSREF] GET {BASE_URL} params={params}")
        try:
            r = await client.get(BASE_URL, params=params)
            logger.info(f"[CROSSREF] Response status: {r.status_code}")
            
            if r.status_code != 200:
                logger.error(f"[CROSSREF] Error: {r.text}")
                return []
                
            data = r.json()
        except Exception as e:
            logger.error(f"[CROSSREF] Exception: {e}")
            return []

    items = data.get("message", {}).get("items", [])
    articles = []

    for item in items:
        # DOI
        doi = item.get("DOI", "")
        if not doi:
            continue
            
        # Título
        titles = item.get("title", [])
        title = titles[0] if titles else "Sin título"
        
        # Autores
        authors_list = item.get("author", [])
        authors = []
        for auth in authors_list:
            given = auth.get("given", "")
            family = auth.get("family", "")
            name = f"{given} {family}".strip()
            if name:
                authors.append({"name": name})
        
        # Journal / Container
        containers = item.get("container-title", [])
        journal = containers[0] if containers else "CrossRef"
        
        # Fecha creation
        created = item.get("created", {})
        date_parts = created.get("date-parts", [[]])[0]
        pub_date = "-".join(map(str, date_parts)) if date_parts else ""
        
        # URL
        url = item.get("URL") or f"https://doi.org/{doi}"
        
        # Snippet / Abstract
        # CrossRef a veces tiene abstract jats:abstract. Es XML embebido.
        # Por simplicidad usaremos el título.
        snippet = title
        
        articles.append({
            "id": doi,
            "source": "crossref",
            "title": title,
            "authors": authors,
            "journal": journal,
            "pub_date": pub_date,
            "doi": doi,
            "url": url,
            "snippet": snippet,
        })

    logger.info(f"[CROSSREF] Found {len(articles)} articles")
    return articles
