# 🔍 Buscador de Artículos Científicos (AI-Powered)

Una herramienta avanzada para investigadores que permite buscar en múltiples fuentes académicas simultáneamente, filtrar resultados mediante Inteligencia Artificial (Google Gemini) y gestionar tu biblioteca personal de Zotero de forma automática.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Node](https://img.shields.io/badge/node-18%2B-green.svg)

---

## 🚀 Inicio Rápido

### Requisitos Previos

Para ejecutar este proyecto, asegúrate de tener instalado:

- [Python 3.10 o superior](https://www.python.org/downloads/)
- [Node.js 18 o superior](https://nodejs.org/)
- Una cuenta en [Zotero](https://www.zotero.org/)

### 1. Configuración del Backend

1. Entra a la carpeta del servidor y crea un entorno virtual:
   ```bash
   cd backend
   python -m venv venv
   ```
2. Activa el entorno:
   - **Windows:** `venv\Scripts\activate`
   - **Linux/macOS:** `source venv/bin/activate`
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura tus variables de entorno (ver sección [🔑 API Keys](#-obtención-de-api-keys)).

### 2. Configuración del Frontend

1. En una nueva terminal, entra a la carpeta del cliente:
   ```bash
   cd frontend
   npm install
   ```
2. Inicia el servidor de desarrollo:
   ```bash
   npm run dev
   ```

---

## 🔑 Obtención de API Keys

Para que el sistema funcione a pleno rendimiento, necesitarás configurar las siguientes llaves en un archivo `.env` dentro de la carpeta `backend/`:

| Servicio           | Propósito                    | Dónde obtenerla                                                                        |
| :----------------- | :--------------------------- | :------------------------------------------------------------------------------------- |
| **Google Gemini**  | Filtrado por IA y Relevancia | [Google AI Studio](https://aistudio.google.com/app/apikey)                             |
| **Zotero API Key** | Guardado de referencias      | [Zotero Settings](https://www.zotero.org/settings/keys)                                |
| **Zotero User ID** | Identificar tu biblioteca    | [Zotero Settings](https://www.zotero.org/settings/keys) (Aparece arriba de las llaves) |
| **Scopus**         | Fuente adicional (Opcional)  | [Elsevier Dev Portal](https://dev.elsevier.com/)                                       |
| **Springer**       | Fuente adicional (Opcional)  | [Springer Nature API](https://dev.springernature.com/)                                 |

### Ejemplo de archivo `.env`:

```env
GEMINI_API_KEY=tu_clave_aqui
ZOTERO_API_KEY=tu_clave_aqui
ZOTERO_USER_ID=tu_id_aqui
SCOPUS_API_KEY=opcional
SPRINGER_API_KEY=opcional
```

---

## 🛠️ Estructura del Proyecto

### Backend (FastAPI)

- `app/main.py`: Corazón de la API.
- `app/services/llm_filter.py`: Lógica del filtro de IA con Gemini.
- `app/services/zotero.py`: Integración con la API de Zotero.
- `app/routers/search.py`: Orquestador de búsquedas multicanal.

### Frontend (TypeScript + Vite)

- `src/main.ts`: Lógica de la interfaz y comunicación con el backend.
- `src/style.css`: Diseño moderno con soporte para tema oscuro.

---

## 🧪 Pruebas Automatizadas

El proyecto utiliza **Playwright** para asegurar que todo funcione correctamente.

1. Instala los navegadores necesarios:
   ```bash
   cd backend
   playwright install
   ```
2. Ejecuta los tests:
   ```bash
   pytest tests/e2e
   ```

---

## 🤝 Contribuciones e Incidentes

Si encuentras algún problema o tienes sugerencias:

1. Revisa si el error es **429 (Límite de cuota)** en Gemini; el sistema reintenta automáticamente.
2. Asegúrate de que tu `ZOTERO_API_KEY` tenga permisos de **escritura**.

---

Desarrollado para el Seminario de Posgrado en Ciencias y Tecnologías de la Información (UAM).
