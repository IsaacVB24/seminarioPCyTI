"""Búsqueda en Springer Nature."""
import logging
import os
import json
import urllib.request
import urllib.parse
from typing import Optional

logger = logging.getLogger(__name__)

# Documentation: https://dev.springernature.com/
SPRINGER_API_URL = "http://api.springernature.com/meta/v2/json"

async def search_springer(
    query: str,
    max_results: int = 20,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict]:
    """
    Busca en API de Springer Nature.
    Requiere API Key en variable de entorno SPRINGER_API_KEY.
    """
    api_key = os.getenv("SPRINGER_API_KEY")
    if not api_key:
        logger.warning("[SPRINGER] API Key missing. Skipping search.")
        return [{"error": "springer", "message": "API Key no configurada (SPRINGER_API_KEY missing)"}]

    logger.info(f"[SPRINGER] Searching: '{query}' (max_results={max_results})")
    
    # Try using 'keyword:' constraint which is safer than title/abstract for Meta API
    # and improves relevance significantly over broad full-text search.
    # constraint: type:Journal is also good but optional.
    springer_query = f"keyword:{query}"
    
    if from_date:
        start_date = from_date
        end_date = to_date if to_date else "2030-12-31" 
        springer_query += f" date:{start_date}/{end_date}"

    params = {
        "q": springer_query,
        "p": min(max_results, 100),
        "api_key": api_key,
        "s": 1, 
    }

    query_string = urllib.parse.urlencode(params)
    url = f"{SPRINGER_API_URL}?{query_string}"

    try:
        # Springer API usually works over HTTP/HTTPS. 
        # urllib might need a User-Agent.
        headers = {
            "User-Agent": "SeminarioResearch/1.0"
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            if response.getcode() != 200:
                logger.error(f"[SPRINGER] Error {response.getcode()}")
                return [{"error": "springer", "message": f"Error API: {response.getcode()}"}]
            
            body = response.read().decode('utf-8')
            data = json.loads(body)
            
    except urllib.request.HTTPError as e:
        logger.error(f"[SPRINGER] HTTP Error: {e.code} {e.reason}")
        if e.code in [401, 403]:
             return [{"error": "springer", "message": "Acceso denegado (401/403). Verifique API Key."}]
        return [{"error": "springer", "message": f"Error HTTP: {e.code}"}]
    except Exception as e:
        logger.error(f"[SPRINGER] Connection error: {e}")
        return [{"error": "springer", "message": f"Error de conexión: {str(e)}"}]

    articles = []
    
    records = data.get("records", [])
    
    for item in records:
        try:
            title = item.get("title", "Sin título")
            
            creators = item.get("creators", [])
            authors = []
            for creator in creators:
                if isinstance(creator, dict) and "creator" in creator:
                     authors.append({"name": creator["creator"]})
                else:
                    authors.append({"name": str(creator)})
            
            journal = item.get("publicationName", "Springer")
            pub_date = item.get("publicationDate", "")
            doi = item.get("doi", "")
            
            url = ""
            urls = item.get("url", [])
            # Usually format is [{"format": "html", "value": "..."}]
            for u in urls:
                if u.get("format") == "html":
                    url = u.get("value")
                    break
            
            if not url and urls:
                 url = urls[0].get("value")

            if not url and doi:
                url = f"https://doi.org/{doi}"
                
            snippet = item.get("abstract", "") or title
            # Truncate to avoid long texts in UI
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            
            item_id = item.get("identifier", "") or doi

            articles.append({
                "id": item_id,
                "source": "springer",
                "title": title,
                "authors": authors,
                "journal": journal,
                "pub_date": pub_date,
                "doi": doi,
                "url": url,
                "snippet": snippet,
            })
        except Exception as e:
            logger.warning(f"[SPRINGER] Error parsing item: {e}")
            continue

    logger.info(f"[SPRINGER] Found {len(articles)} articles")
    return articles
