"""Búsqueda en OpenAlex."""
import logging
import urllib.request
import urllib.parse
import json
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
    Busca en OpenAlex using urllib.
    Reference: https://docs.openalex.org/api-entities/works/search-works
    """
    logger.info(f"[OPENALEX] Searching for: '{query}' (max_results={max_results})")
    
    params = {
        "search": query,
        "per-page": min(max_results, 100),
        "mailto": "researcher@seminariopcyt.edu.mx" 
    }

    filters = []
    if from_date:
        filters.append(f"from_publication_date:{from_date}")
    if to_date:
        filters.append(f"to_publication_date:{to_date}")
        
    if filters:
        params["filter"] = ",".join(filters)

    headers = {
        "User-Agent": "SeminarioResearch/1.0 (mailto:researcher@seminariopcyt.edu.mx)"
    }
    
    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}?{query_string}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            logger.info(f"[OPENALEX] Response status: {response.getcode()}")
            if response.getcode() != 200:
                logger.error(f"[OPENALEX] Error {response.getcode()}")
                return [{"error": "openalex", "message": f"Error API: {response.getcode()}"}]
            
            body = response.read().decode('utf-8')
            data = json.loads(body)
            
    except Exception as e:
        logger.error(f"[OPENALEX] Connection error: {e}")
        return [{"error": "openalex", "message": f"Error de conexión: {str(e)}"}]

    results = data.get("results", [])
    articles = []

    for item in results:
        oa_id = item.get("id", "")
        short_id = oa_id.split("/")[-1] if oa_id else ""
        
        title = item.get("display_name") or item.get("title") or "Sin título"
        
        authorships = item.get("authorships", [])
        authors = []
        for auth in authorships:
            author_obj = auth.get("author", {})
            name = author_obj.get("display_name", "")
            if name:
                authors.append({"name": name})
        
        primary_loc = item.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        journal = source.get("display_name") or "OpenAlex"
        
        pub_date = item.get("publication_date", "") or str(item.get("publication_year", ""))
        
        doi = item.get("doi")
        url = doi or oa_id 
        
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
