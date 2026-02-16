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

def _format_zotero_item(article: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to format a single article for Zotero."""
    zotero_item = {
        "itemType": "journalArticle",
        "title": article.get("title", "Sin título"),
        "creators": [],
        "publicationTitle": article.get("journal", ""),
        "date": article.get("pub_date", ""),
        "url": article.get("url", ""),
        "abstractNote": article.get("snippet", ""),
        "DOI": article.get("doi", ""),
        "libraryCatalog": article.get("source", "") # Store original source here
    }

    for auth in article.get("authors", []):
        name = auth.get("name", "")
        if " " in name:
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
    return zotero_item

async def save_batch_to_zotero(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Save multiple articles to Zotero, checking for duplicates."""
    api_key = os.getenv("ZOTERO_API_KEY", "").strip()
    user_id = os.getenv("ZOTERO_USER_ID", "").strip()

    if not api_key or not user_id:
        return {"error": "Faltan credenciales de Zotero"}

    saved_count = 0
    skipped_count = 0
    errors = []
    items_to_send = []

    # 1. Filter duplicates locally first to avoid hammering API?
    # No, we must check API.
    
    for article in articles:
        title = article.get("title", "")
        if not title:
            continue
            
        try:
            if await check_duplicate(title, user_id, api_key):
                skipped_count += 1
                continue
        except Exception as e:
            logger.error(f"Error checking duplicate for {title}: {e}")
            # Try to save anyway? Or skip? Skip to be safe.
            errors.append(f"Error checking dup: {title}")
            continue

        items_to_send.append(_format_zotero_item(article))

    # 2. Send in batches (limit 50 per request)
    chunk_size = 50
    endpoint = f"{ZOTERO_API_URL}/users/{user_id}/items"

    for i in range(0, len(items_to_send), chunk_size):
        chunk = items_to_send[i:i + chunk_size]
        payload = json.dumps(chunk).encode('utf-8')
        
        try:
            req = urllib.request.Request(endpoint, data=payload, headers=get_headers(api_key), method="POST")
            with urllib.request.urlopen(req) as response:
                if response.getcode() in [200, 201]:
                    resp_data = json.loads(response.read().decode('utf-8'))
                    if "successful" in resp_data:
                        saved_count += len(resp_data["successful"])
                    if "failed" in resp_data and resp_data["failed"]:
                         errors.append(f"Failed items: {json.dumps(resp_data['failed'])}")
                else:
                    errors.append(f"Batch error: {response.getcode()}")
        except urllib.error.HTTPError as e:
             err_txt = e.read().decode('utf-8')
             logger.error(f"Zotero Batch Error: {err_txt}")
             errors.append(f"HTTP Error: {e.code}")
        except Exception as e:
            errors.append(f"Exception: {str(e)}")

    return {
        "saved": saved_count,
        "skipped": skipped_count,
        "errors": errors
    }

async def save_to_zotero(article: Dict[str, Any]) -> Dict[str, Any]:
    """Save an article to Zotero."""
    api_key = os.getenv("ZOTERO_API_KEY", "").strip()
    user_id = os.getenv("ZOTERO_USER_ID", "").strip()

    if not api_key or not user_id:
        return {"error": "Configuración incompleta (Faltan claves Zotero)"}

    # Check for duplicates
    if await check_duplicate(article.get("title", ""), user_id, api_key):
        return {"error": "El artículo ya existe en tu biblioteca Zotero."}

    endpoint = f"{ZOTERO_API_URL}/users/{user_id}/items"
    zotero_item = _format_zotero_item(article)
    payload = json.dumps([zotero_item]).encode('utf-8')
    
    try:
        req = urllib.request.Request(endpoint, data=payload, headers=get_headers(api_key), method="POST")
        with urllib.request.urlopen(req) as response:
            if response.getcode() in [200, 201]:
                resp_data = json.loads(response.read().decode('utf-8'))
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
