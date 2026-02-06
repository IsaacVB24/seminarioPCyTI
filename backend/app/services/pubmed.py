"""Búsqueda en PubMed (biomedicina y ciencias de la vida)."""
import httpx
from typing import Optional

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


async def search_pubmed(
    query: str,
    max_results: int = 20,
    sort: str = "relevance",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    Busca en PubMed. Orden: relevance, pub_date, first_author, journal, title.
    from_date/to_date formato YYYY/MM/DD.
    """
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": min(max_results, 100),
        "sort": sort,
        "retmode": "json",
    }
    if from_date:
        params["mindate"] = from_date.replace("-", "/")
    if to_date:
        params["maxdate"] = to_date.replace("-", "/")
    if api_key:
        params["api_key"] = api_key

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{BASE}/esearch.fcgi", params=params)
        r.raise_for_status()
        data = r.json()
    id_list = data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return []

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{BASE}/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(id_list), "retmode": "json"},
        )
        r.raise_for_status()
        data = r.json()

    result = data.get("result", {})
    articles = []
    for pid in id_list:
        item = result.get(pid, {})
        articles.append({
            "id": pid,
            "source": "pubmed",
            "title": item.get("title", ""),
            "authors": item.get("authors", []),
            "journal": item.get("source", ""),
            "pub_date": item.get("pubdate", ""),
            "doi": item.get("elocationid", "").replace("doi: ", "") or None,
            "pmid": pid,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
            "snippet": item.get("title", ""),
        })
    return articles
