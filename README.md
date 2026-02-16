# Buscador de Artículos Científicos

Aplicación para buscar artículos científicos en múltiples fuentes simultáneamente, filtrarlos con Inteligencia Artificial (Google Gemini) y guardarlos en tu biblioteca personal de Zotero.

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
- **API Keys**:
  - `GEMINI_API_KEY`: **Requerido** para el filtrado por IA y cálculo de relevancia.
  - `ZOTERO_API_KEY`: **Requerido** para guardar referencias.
  - `ZOTERO_USER_ID`: **Requerido** para identificar tu biblioteca.
  - `SCOPUS_API_KEY`: (Opcional) Para Scopus.
  - `SPRINGER_API_KEY`: (Opcional) Para Springer Link.

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
# IA
GEMINI_API_KEY=tu_clave_gemini

# Zotero (Gestión de referencias)
ZOTERO_API_KEY=tu_clave_zotero_con_permisos_write
ZOTERO_USER_ID=tu_user_id_zotero

# Bibliográficas (Opcionales)
SCOPUS_API_KEY=tu_clave_scopus
SPRINGER_API_KEY=tu_clave_springer
```

El API estará disponible en: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 2. Frontend (TypeScript / Vite)

En una nueva terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre [http://localhost:5173](http://localhost:5173) en tu navegador.

## Uso

1.  **Búsqueda**: Ingresa términos, selecciona fuentes y filtros.
2.  **Filtro IA**: Activa "🤖 Filtrar con IA" para que Google Gemini analice la relevancia de cada artículo según tu contexto.
3.  **Guardar**:
    - Usa el botón "💾 Guardar" en cada tarjeta para guardar individualmente.
    - Usa "💾 Guardar todos los resultados en Zotero" para guardar en lote (detecta duplicados automáticamente).
4.  **Biblioteca**: Haz clic en "📚 Mis Referencias" para ver lo que has guardado en Zotero.

## Estructura del Proyecto y Archivos Relevantes

### Backend (`backend/`)

- **`app/main.py`**: Punto de entrada de la aplicación FastAPI. Configura CORS e incluye los routers.
- **`app/routers/`**:
  - **`search.py`**: Maneja el endpoint `/search`. Orquesta las llamadas a todas las APIs académicas y la llamada posterior al filtro LLM.
  - **`zotero.py`**: Maneja endpoints para Zotero (`/zotero/items`, `/zotero/items/batch`). Conecta el frontend con el servicio de Zotero.
- **`app/services/`**: Lógica de negocio e integraciones.
  - **`llm_filter.py`**: **CRÍTICO**. Implementa la conexión con Google Gemini. Contiene el prompt de sistema, lógica de reintento para error 429 (cuota excedida) y parseo de la respuesta JSON para asignar puntajes de relevancia.
  - **`zotero.py`**: Gestiona la comunicación con la API de Zotero. Formatea los artículos al esquema de Zotero, verifica duplicados por título y maneja el guardado por lotes.
  - **`arxiv.py`, `crossref.py`, etc.**: Módulos individuales para buscar en cada fuente académica. Usan `urllib` para máxima estabilidad.
- **`clear_zotero_library.py`**: Script de utilidad para **BORRAR** todas las referencias de la biblioteca Zotero configurada. Útil para reiniciar pruebas.

### Frontend (`frontend/`)

- **`index.html`**: Estructura HTML principal. Contiene el formulario de búsqueda, el contenedor de resultados y la vista de biblioteca.
- **`src/main.ts`**: **Lógica Principal**.
  - Maneja eventos del DOM (búsqueda, botones de guardar).
  - Renderiza las tarjetas de artículos (incluyendo badges de IA y fuentes).
  - Gestiona la navegación entre la vista de búsqueda y la de biblioteca.
  - Implementa el sistema de notificaciones (Toasts).
- **`src/style.css`**: Estilos globales. Define el tema oscuro, diseño de tarjetas, animaciones de toasts y badges de colores para cada fuente y nivel de relevancia.

## Notas Técnicas y Solución de Problemas

- **Error 429 (IA)**: Si ves que el filtro de IA tarda o falla, es probable que hayas excedido la cuota gratuita de Gemini. El sistema reintentará automáticamente (esperando 10s, 20s, 40s), pero puede requerir espera manual.
- **Zotero**: Asegúrate de que tu `ZOTERO_API_KEY` tenga permisos de **lectura y escritura** para la biblioteca.
- **Semantic Scholar**: Tiene límites de tasa por IP. Si falla, espera unos minutos.
## Pruebas Automatizadas (E2E)

El proyecto incluye pruebas de extremo a extremo (End-to-End) usando **Playwright** y **Pytest** para verificar el flujo completo de la aplicación (búsqueda, guardado en Zotero, filtros).

### Ejecución de Pruebas

1.  Asegúrate de estar en la carpeta `backend` (donde está el archivo `requirements.txt`):

    ```bash
    cd backend
    ```

2.  Instala las dependencias y los navegadores (si no lo has hecho):

    ```bash
    pip install -r requirements.txt
    playwright install
    ```

3.  Asegúrate de que tu aplicación esté corriendo:
    - Backend: `uvicorn app.main:app --reload` (en puerto 8000)
    - Frontend: `npm run dev` (en puerto 5173)

4.  Ejecuta las pruebas:

    ```bash
    pytest tests/e2e
    ```

    Para ver el navegador mientras se ejecutan las pruebas (modo "headed"):

    ```bash
    pytest tests/e2e --headed
    ```

> **Nota**: Las pruebas interactúan con los servicios reales (Zotero, Gemini), por lo que crearán elementos en tu biblioteca de Zotero. Puedes usar `python clear_zotero_library.py` para limpiar después.
