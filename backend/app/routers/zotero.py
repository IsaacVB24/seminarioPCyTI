"""Rutas para integración con Zotero."""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from app.services.zotero import get_zotero_items, save_to_zotero

router = APIRouter()

@router.get("/items")
async def list_items():
    """Listar artículos de Zotero."""
    items = await get_zotero_items()
    # Simplificar para el frontend
    simplified = []
    for item in items:
        data = item.get("data", {})
        
        # Parse creators to string
        creators = data.get("creators", [])
        authors_str = ", ".join([f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() for c in creators])
        
        simplified.append({
            "id": data.get("key"), # Zotero Item Key
            "title": data.get("title"),
            "authors": authors_str,
            "journal": data.get("publicationTitle", ""),
            "pub_date": data.get("date", ""),
            "url": data.get("url", ""),
            "doi": data.get("DOI", ""),
            "source": "zotero",
            "snippet": data.get("abstractNote", "") # Add snippet too
        })
    print(f"[ROUTER] Zotero items found: {len(simplified)}")
    return simplified

@router.post("/items")
async def save_item(article: Dict[str, Any] = Body(...)):
    """Guardar artículo en Zotero."""
    result = await save_to_zotero(article)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
