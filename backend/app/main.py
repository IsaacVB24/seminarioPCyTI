"""
Backend para búsqueda de artículos científicos.
Fuentes: PubMed, arXiv, Semantic Scholar.
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.routers import search

app = FastAPI(
    title="Buscador de Artículos Científicos",
    description="API para buscar en PubMed, arXiv y Semantic Scholar según criterios de investigación.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api", tags=["search"])


@app.get("/")
def root():
    return {"message": "API de búsqueda de artículos científicos. Ver /docs para documentación."}
