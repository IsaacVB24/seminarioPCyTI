"""Búsqueda en Elsevier Scopus."""
import logging
import os
import json
import urllib.request
import urllib.parse
from typing import Optional

logger = logging.getLogger(__name__)

# Documentation: https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
SCOPUS_API_URL = "https://api.elsevier.com/content/search/scopus"

async def search_scopus(
    query: str,
    max_results: int = 20,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    sort_by: str = "relevance",
) -> list[dict]:
    """
    Busca en API de Scopus.
    Requiere API Key en variable de entorno SCIENCEDIRECT_API_KEY (por compatibilidad) o SCOPUS_API_KEY.
    Using urllib to avoid dependency issues.
    """
    api_key = os.getenv("SCOPUS_API_KEY") or os.getenv("SCIENCEDIRECT_API_KEY")
    if not api_key:
        logger.warning("[SCOPUS] API Key missing. Skipping search.")
        return [{"error": "scopus", "message": "API Key no configurada (SCOPUS_API_KEY missing)"}]

    logger.info(f"[SCOPUS] Searching: '{query}' (max_results={max_results}, sort={sort_by})")
    
    # Mejora de relevancia: buscar en Título, Abstract y Keywords
    scopus_query = f"TITLE-ABS-KEY({query})"
    
    # Mapeo de ordenamiento
    api_sort = "relevance"
    if sort_by == "pub_date":
        api_sort = "-coverDate"
    
    params = {
        "query": scopus_query,
        "count": min(max_results, 100),
        "httpAccept": "application/json",
        "apiKey": api_key,
        "sort": api_sort
    }
    
    # Filtro de fecha para Scopus (pubyear)
    if from_date:
        params["query"] += f" AND PUBYEAR > {int(from_date[:4]) - 1}"

    headers = {
        "X-ELS-APIKey": api_key,
        "User-Agent": "SeminarioResearch/1.0",
        "Accept": "application/json"
    }
    
    query_string = urllib.parse.urlencode(params)
    url = f"{SCOPUS_API_URL}?{query_string}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            logger.info(f"[SCOPUS] Response status: {response.getcode()}")
            
            if response.getcode() != 200:
                logger.error(f"[SCOPUS] Error {response.getcode()}")
                return [{"error": "scopus", "message": f"Error API: {response.getcode()}"}]
            
            body = response.read().decode('utf-8')
            data = json.loads(body)
            
    except urllib.request.HTTPError as e:
        logger.error(f"[SCOPUS] HTTP Error: {e.code} {e.reason}")
        if e.code in [401, 403]:
             return [{"error": "scopus", "message": "Acceso denegado (401/403). Verifique API Key."}]
        return [{"error": "scopus", "message": f"Error HTTP: {e.code}"}]
    except Exception as e:
        logger.error(f"[SCOPUS] Connection error: {e}")
        return [{"error": "scopus", "message": f"Error de conexión: {str(e)}"}]

    articles = []
    
    search_results = data.get("search-results", {})
    entries = search_results.get("entry", [])
    
    for item in entries:
        try:
            title = item.get("dc:title", "Sin título")
            
            creator = item.get("dc:creator")
            authors = []
            if creator:
                authors.append({"name": str(creator)})
            
            journal = item.get("prism:publicationName", "Elsevier")
            pub_date = item.get("prism:coverDate", "") or item.get("prism:coverDisplayDate", "")
            doi = item.get("prism:doi", "")
            
            # Links
            links = item.get("link", [])
            url = ""
            for link in links:
                if link.get("@ref") == "scopus":
                    url = link.get("@href", "")
                    break
            
            if not url and doi:
                url = f"https://doi.org/{doi}"
                
            snippet = item.get("dc:description", "") or title
            
            item_id = item.get("dc:identifier", "") or doi

            articles.append({
                "id": item_id,
                "source": "scopus",
                "title": title,
                "authors": authors,
                "journal": journal,
                "pub_date": pub_date,
                "doi": doi,
                "url": url,
                "snippet": snippet,
            })
        except Exception as e:
            logger.warning(f"[SCOPUS] Error parsing item: {e}")
            continue

    logger.info(f"[SCOPUS] Found {len(articles)} articles")
    return articles
