"""Búsqueda en arXiv (física, matemáticas, CS, etc.)."""
import httpx
import logging
from typing import Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

ARXiv_NS = {"atom": "http://www.w3.org/2005/Atom"}


async def search_arxiv(
    query: str,
    max_results: int = 20,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict]:
    """
    Busca en arXiv. sort_by: relevance, lastUpdatedDate, submittedDate.
    sort_order: ascending, descending.
    """
    logger.info(f"[ARXIV] Searching for: '{query}' (max_results={max_results})")
    
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(max_results, 100),
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }

    headers = {"User-Agent": "SeminarioResearch/1.0"}

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        url = "https://export.arxiv.org/api/query"
        logger.debug(f"[ARXIV] GET {url}")
        r = await client.get(url, params=params)
        logger.info(f"[ARXIV] Response status: {r.status_code}")
        r.raise_for_status()
        root = ET.fromstring(r.text)

    articles = []
    for entry in root.findall("atom:entry", ARXiv_NS):
        arxiv_id = entry.find("atom:id", ARXiv_NS)
        id_url = arxiv_id.text.strip() if arxiv_id is not None and arxiv_id.text else ""
        arxiv_id_short = id_url.split("/abs/")[-1].rstrip("/") if "/abs/" in id_url else ""

        title_el = entry.find("atom:title", ARXiv_NS)
        title = title_el.text.strip().replace("\n", " ") if title_el is not None and title_el.text else ""

        summary_el = entry.find("atom:summary", ARXiv_NS)
        snippet = summary_el.text.strip()[:300] + "..." if summary_el is not None and summary_el.text else title

        published = entry.find("atom:published", ARXiv_NS)
        pub_date = published.text[:10] if published is not None and published.text else ""

        authors = []
        for author in entry.findall("atom:author", ARXiv_NS):
            name_el = author.find("atom:name", ARXiv_NS)
            if name_el is not None and name_el.text:
                authors.append({"name": name_el.text.strip()})

        link_pdf = ""
        for link in entry.findall("atom:link", ARXiv_NS):
            if link.get("title") == "pdf":
                link_pdf = link.get("href", "")
                break

        articles.append({
            "id": arxiv_id_short,
            "source": "arxiv",
            "title": title,
            "authors": authors,
            "journal": "arXiv",
            "pub_date": pub_date,
            "doi": None,
            "url": f"https://arxiv.org/abs/{arxiv_id_short}",
            "pdf_url": link_pdf or f"https://arxiv.org/pdf/{arxiv_id_short}.pdf",
            "snippet": snippet,
        })
    
    logger.info(f"[ARXIV] Found {len(articles)} articles")
    return articles
