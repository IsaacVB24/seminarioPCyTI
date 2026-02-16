"""Service for interacting with Zotero API."""
import logging
import os
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

ZOTERO_API_URL = "https://api.zotero.org"

def get_headers(api_key: str) -> Dict[str, str]:
    return {
        "Zotero-API-Key": api_key,
        "Content-Type": "application/json"
    }

async def get_zotero_items(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch items from Zotero library."""
    api_key = os.getenv("ZOTERO_API_KEY", "").strip()
    user_id = os.getenv("ZOTERO_USER_ID", "").strip()

    if not api_key or not user_id:
        logger.warning("[ZOTERO] Credentials missing (ZOTERO_API_KEY or ZOTERO_USER_ID).")
        return []

    # Default to 'users' but could be 'groups' if user_id starts with 'G' (convention?) 
    # For now assume 'users'.
    endpoint = f"{ZOTERO_API_URL}/users/{user_id}/items"
    
    params = {
        "format": "json",
        "limit": limit,
        "sort": "dateAdded",
        "direction": "desc",
        "itemType": "-attachment || note" # Exclude attachments and notes
    }
    
    query_string = urllib.parse.urlencode(params)
    url = f"{endpoint}?{query_string}"
    
    try:
        req = urllib.request.Request(url, headers=get_headers(api_key))
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data
            else:
                logger.error(f"[ZOTERO] Error fetching items: {response.getcode()}")
                return []
    except Exception as e:
        logger.error(f"[ZOTERO] Connection error: {e}")
        return []

async def check_duplicate(title: str, user_id: str, api_key: str) -> bool:
    """Check if an item with the same title already exists."""
    endpoint = f"{ZOTERO_API_URL}/users/{user_id}/items"
    # Search by title (q parameter or specific field search if possible, q is easiest)
    # Zotero 'q' searches everything. precision is low but good for quick check.
    # Better: use 'q' and filter locally or trust zotero relevant sort.
    # Actually, simply checking if title exists in a search is decent.
    
    params = {
        "q": title,
        "limit": 5,
        "format": "json"
    }
    query_string = urllib.parse.urlencode(params)
    url = f"{endpoint}?{query_string}"
    
    try:
        req = urllib.request.Request(url, headers=get_headers(api_key))
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                items = json.loads(response.read().decode('utf-8'))
                # Verify exact title match to be sure
                norm_title = title.lower().strip()
                for item in items:
                    item_title = item.get("data", {}).get("title", "").lower().strip()
                    if item_title == norm_title:
                        return True
                return False
    except Exception as e:
        logger.error(f"[ZOTERO] Duplicate check error: {e}")
        return False
    return False

async def save_to_zotero(article: Dict[str, Any]) -> Dict[str, Any]:
    """Save an article to Zotero."""
    api_key = os.getenv("ZOTERO_API_KEY")
    user_id = os.getenv("ZOTERO_USER_ID")

    if not api_key or not user_id:
        return {"error": "Configuración incompleta (Faltan claves Zotero)"}

    # Check for duplicates
    if await check_duplicate(article.get("title", ""), user_id, api_key):
        return {"error": "El artículo ya existe en tu biblioteca Zotero."}

    endpoint = f"{ZOTERO_API_URL}/users/{user_id}/items"
    
    # Map article to Zotero format (journalArticle)
    # Reference: https://www.zotero.org/support/dev/web_api/v3/basics
    
    zotero_item = {
        "itemType": "journalArticle",
        "title": article.get("title", "Sin título"),
        "creators": [],
        "publicationTitle": article.get("journal", ""),
        "date": article.get("pub_date", ""),
        "url": article.get("url", ""),
        "abstractNote": article.get("snippet", ""),
        "DOI": article.get("doi", "")
    }

    # Format authors
    for auth in article.get("authors", []):
        name = auth.get("name", "")
        if " " in name:
            # Simple heuristic splitting
            parts = name.split(" ")
            first = " ".join(parts[:-1])
            last = parts[-1]
            zotero_item["creators"].append({
                "creatorType": "author",
                "firstName": first,
                "lastName": last
            })
        else:
            zotero_item["creators"].append({
                "creatorType": "author",
                "lastName": name,
                "firstName": ""
            })

    # Body must be a list of items
    payload = json.dumps([zotero_item]).encode('utf-8')
    
    try:
        req = urllib.request.Request(endpoint, data=payload, headers=get_headers(api_key), method="POST")
        with urllib.request.urlopen(req) as response:
            if response.getcode() in [200, 201]:
                resp_data = json.loads(response.read().decode('utf-8'))
                # Response checks
                if resp_data.get("successful"):
                    return {"success": True, "data": resp_data["successful"]}
                else:
                    return {"error": "Fallo al guardar en Zotero (API reportó fallo)"}
            else:
                return {"error": f"Error Zotero API: {response.getcode()}"}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        logger.error(f"[ZOTERO] HTTP Error {e.code}: {error_body}")
        return {"error": f"Error Zotero {e.code}: {error_body}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Excepción al guardar: {str(e)}"}
