"""
Backend para búsqueda de artículos científicos.
Fuentes: arXiv, Semantic Scholar.
"""
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Buscador de Artículos Científicos",
    description="API para buscar en arXiv y Semantic Scholar según criterios de investigación.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["search"])


@app.get("/")
def root():
    return {"message": "API de búsqueda de artículos científicos. Ver /docs para documentación."}
