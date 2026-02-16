"""Búsqueda en CrossRef."""
import logging
import urllib.request
import urllib.parse
import json
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://api.crossref.org/works"

async def search_crossref(
    query: str,
    max_results: int = 20,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict]:
    """Busca en CrossRef using urllib."""
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
    
    # CrossRef params might need proper encoding, urllib handles dict to query string well.
    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}?{query_string}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            logger.info(f"[CROSSREF] Response status: {response.getcode()}")
            if response.getcode() != 200:
                logger.error(f"[CROSSREF] Error {response.getcode()}")
                return []
            
            body = response.read().decode('utf-8')
            data = json.loads(body)
            
    except Exception as e:
        logger.error(f"[CROSSREF] Exception: {e}")
        return []

    items = data.get("message", {}).get("items", [])
    articles = []

    for item in items:
        doi = item.get("DOI", "")
        if not doi:
            continue
            
        titles = item.get("title", [])
        title = titles[0] if titles else "Sin título"
        
        authors_list = item.get("author", [])
        authors = []
        for auth in authors_list:
            given = auth.get("given", "")
            family = auth.get("family", "")
            name = f"{given} {family}".strip()
            if name:
                authors.append({"name": name})
        
        containers = item.get("container-title", [])
        journal = containers[0] if containers else "CrossRef"
        
        created = item.get("created", {})
        date_parts = created.get("date-parts", [[]])[0]
        pub_date = "-".join(map(str, date_parts)) if date_parts else ""
        
        url = item.get("URL") or f"https://doi.org/{doi}"
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
