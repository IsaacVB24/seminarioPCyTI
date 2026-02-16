# Buscador de Artículos Científicos

Aplicación para buscar artículos científicos en múltiples fuentes simultáneamente. Combina **Python (FastAPI)** en el backend y **TypeScript (Vite)** en el frontend.

## Fuentes Disponibles

1.  **arXiv**: Preprints de física, matemáticas, CS, etc.
2.  **Semantic Scholar**: Multidisciplinario con análisis de citas.
3.  **OpenAlex**: Catálogo global de obras, autores e instituciones.
4.  **CrossRef**: Metadatos de DOIs y publicaciones académicas.
5.  **Scopus**: Base de datos de Elsevier (Requiere API Key).
6.  **Springer Link**: Publicaciones de Springer Nature (Requiere API Key).

## Requisitos

- **Python 3.10+**
- **Node.js 18+** (para el frontend)
- **API Keys** (opcionales pero recomendadas):
  - `SCOPUS_API_KEY`: Para Scopus.
  - `SPRINGER_API_KEY`: Para Springer Link.
  - `GEMINI_API_KEY`: (Opcional) Para filtrado inteligente con LLM.

## Instalación

### 1. Backend (Python)

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # Iniciar servidor
```

Crea un archivo `.env` en la carpeta `backend/` con tus claves:

```env
SCOPUS_API_KEY=tu_clave_scopus
SPRINGER_API_KEY=tu_clave_springer
GEMINI_API_KEY=tu_clave_gemini
```

El API estará disponible en: [http://127.0.0.1:8000](http://127.0.0.1:8000)  
Documentación interactiva (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend (TypeScript / Vite)

En una nueva terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre [http://localhost:5173](http://localhost:5173) en tu navegador.

## Uso

1.  Ingresa tus términos de búsqueda (ej. "software engineering", "machine learning").
2.  Selecciona las fuentes deseadas.
3.  (Opcional) Configura rango de fechas o filtro por relevancia.
4.  Define el máximo de resultados (hasta 100).
5.  Haz clic en **Buscar**.

Los resultados mostrarán:

- Título y enlace al artículo/PDF.
- Autores, fecha y revista/fuente.
- Resumen (snippet) truncado a 300 caracteres.
- Badge de la fuente (con código de colores).

## Estructura del Proyecto

```
Carpeta raíz/
├── backend/
│   ├── app/
│   │   ├── main.py           # Configuración FastAPI
│   │   ├── routers/
│   │   │   └── search.py     # Lógica de búsqueda unificada
│   │   └── services/         # Integraciones con APIs externas
│   │       ├── arxiv.py
│   │       ├── semantic_scholar.py
│   │       ├── openalex.py
│   │       ├── crossref.py
│   │       ├── scopus.py
│   │       └── springer.py
│   └── requirements.txt
├── frontend/
│   ├── index.html            # Interfaz principal
│   ├── src/
│   │   ├── main.ts           # Lógica del cliente
│   │   └── style.css         # Estilos
│   └── package.json
└── README.md
```

## Notas Técnicas

- Se utiliza `urllib` (biblioteca estándar de Python) en los servicios para garantizar máxima compatibilidad y estabilidad.
- El límite de resultados se ha aumentado a 100 por búsqueda.
- **Nota sobre Semantic Scholar**: Esta API tiene límites estrictos de tasa (rate limits) basados en IP. Si realizas muchas peticiones consecutivas, es posible que falle temporalmente (Error 429). El sistema incluye lógica de reintento, pero si persiste, espera unos minutos.
