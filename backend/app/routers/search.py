"""Rutas de búsqueda unificada."""
import logging
from fastapi import APIRouter, Query
from typing import Optional

from app.services import search_arxiv, search_semantic_scholar
from app.services.openalex import search_openalex
from app.services.crossref import search_crossref
from app.services.llm_filter import filter_articles_with_llm

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search")
async def search_all(
    q: str = Query(..., min_length=2, description="Términos de búsqueda"),
    sources: str = Query("arxiv,semantic_scholar,openalex,crossref", description="Fuentes: arxiv, semantic_scholar, openalex, crossref"),
    max_results: int = Query(20, ge=1, le=50),
    sort: str = Query("relevance", description="relevance | pub_date"),
    from_date: Optional[str] = Query(None, description="Fecha desde YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="Fecha hasta YYYY-MM-DD"),
    use_llm_filter: bool = Query(False, description="Filtrar resultados con IA"),
    context: Optional[str] = Query(None, description="Contexto adicional para el filtro IA"),
):
    """
    Busca en las fuentes seleccionadas y devuelve resultados normalizados.
    """
    logger.info(f"[SEARCH] Query: '{q}', sources: {sources}, max_results: {max_results}")
    
    chosen = [s.strip().lower() for s in sources.split(",")]
    results = []
    per_source = max(5, max_results // len(chosen)) if chosen else max_results

    if "arxiv" in chosen:
        try:
            results.extend(
                await search_arxiv(
                    query=q,
                    max_results=per_source,
                    sort_by="relevance" if sort == "relevance" else "submittedDate",
                    sort_order="descending",
                    from_date=from_date,
                    to_date=to_date,
                )
            )
        except Exception as e:
            logger.error(f"[SEARCH] Arxiv error: {e}")
            results.append({"error": "arxiv", "message": str(e)})

    if "semantic_scholar" in chosen:
        try:
            results.extend(
                await search_semantic_scholar(
                    query=q,
                    max_results=per_source,
                    from_date=from_date,
                    to_date=to_date,
                )
            )
        except Exception as e:
            logger.error(f"[SEARCH] Semantic Scholar error: {e}")
            results.append({"error": "semantic_scholar", "message": str(e)})

    if "openalex" in chosen:
        try:
            results.extend(
                await search_openalex(
                    query=q,
                    max_results=per_source,
                    from_date=from_date,
                    to_date=to_date,
                )
            )
        except Exception as e:
            logger.error(f"[SEARCH] OpenAlex error: {e}")
            results.append({"error": "openalex", "message": str(e)})

    if "crossref" in chosen:
        try:
            results.extend(
                await search_crossref(
                    query=q,
                    max_results=per_source,
                    from_date=from_date,
                    to_date=to_date,
                )
            )
        except Exception as e:
            logger.error(f"[SEARCH] CrossRef error: {e}")
            results.append({"error": "crossref", "message": str(e)})

    if "scopus" in chosen:
        try:
            from app.services.scopus import search_scopus
            results.extend(
                await search_scopus(
                    query=q,
                    max_results=per_source,
                    from_date=from_date,
                    to_date=to_date,
                    sort_by=sort,
                )
            )
        except Exception as e:
            logger.error(f"[SEARCH] Scopus error: {e}")
            results.append({"error": "scopus", "message": str(e)})

    # Filtrar entradas que son errores para no mezclar con artículos
    errors = [x for x in results if isinstance(x, dict) and "error" in x]
    articles = [x for x in results if isinstance(x, dict) and "source" in x]

    original_count = len(articles)
    
    # Apply LLM filtering if requested
    if use_llm_filter and articles:
        logger.info(f"[SEARCH] Applying LLM filter to {len(articles)} articles")
        try:
            articles = await filter_articles_with_llm(q, articles, context)
            logger.info(f"[SEARCH] LLM filtered to {len(articles)} articles")
        except Exception as e:
            logger.error(f"[SEARCH] LLM filter failed: {e}")
            # Continue with unfiltered results on error

    logger.info(f"[SEARCH] Returning {len(articles)} articles (original: {original_count}), {len(errors)} errors")
    
    return {
        "query": q,
        "total": len(articles),
        "original_total": original_count if use_llm_filter else len(articles),
        "llm_filtered": use_llm_filter,
        "errors": errors,
        "articles": articles[:max_results],
    }
