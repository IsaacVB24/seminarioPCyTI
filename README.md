# Buscador de artículos científicos

Aplicación para buscar artículos científicos según criterios de investigación. Combina **Python** (FastAPI) en el backend y **TypeScript** en el frontend.

## Fuentes de búsqueda

- **PubMed**: biomedicina y ciencias de la vida (NCBI).
- **arXiv**: física, matemáticas, informática, etc.
- **Semantic Scholar**: multidisciplinario.

## Requisitos

- Python 3.10+
- Node.js 18+ (para el frontend)

## Instalación y uso

### 1. Backend (Python)

```bash
cd backend
python -m venv venv
venv\Scripts\activate    # En Windows
# source venv/bin/activate   # En Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload
```

El API quedará en **http://127.0.0.1:8000**. Documentación interactiva: http://127.0.0.1:8000/docs

### 2. Frontend (TypeScript / Vite)

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre **http://localhost:5173** en el navegador. Las peticiones al API se redirigen al backend por el proxy de Vite.

## Criterios de búsqueda

- **Términos**: palabras clave o frase.
- **Fuentes**: marcar PubMed, arXiv y/o Semantic Scholar.
- **Orden**: por relevancia o por fecha de publicación.
- **Rango de fechas**: desde / hasta (opcional).
- **Máximo de resultados**: 5–50 por búsqueda.

## Estructura del proyecto

```
Seminario/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── routers/
│   │   │   └── search.py     # GET /api/search
│   │   └── services/
│   │       ├── pubmed.py
│   │       ├── arxiv.py
│   │       └── semantic_scholar.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── src/
│   │   ├── main.ts
│   │   └── style.css
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## API

- **GET** `/api/search?q=...&sources=pubmed,arxiv,semantic_scholar&max_results=20&sort=relevance&from_date=&to_date=`

Respuesta: `{ "query", "total", "errors", "articles" }`. Cada artículo incluye `title`, `authors`, `journal`, `pub_date`, `url`, `doi`, `source`, `snippet` y, en arXiv, `pdf_url`.

## Opcional: API key de PubMed

Para más solicitudes por segundo puedes usar una API key de NCBI. Pásala como variable de entorno o añade el parámetro en el backend:

- Variable de entorno: `NCBI_API_KEY=tu_clave`

(En el código actual no está integrada; se puede añadir en `app/services/pubmed.py`.)

## Licencia

Uso libre para fines académicos y de investigación.
