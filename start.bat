@echo off
echo ========================================
echo   Iniciando Backend y Frontend
echo ========================================
echo.

:: Iniciar Backend en una nueva ventana
echo [1/2] Iniciando Backend (FastAPI)...
start "Backend - FastAPI" cmd /k "cd /d %~dp0backend && .\venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: Esperar un momento para que el backend inicie primero
timeout /t 3 /nobreak > nul

:: Iniciar Frontend en una nueva ventana
echo [2/2] Iniciando Frontend (Vite)...
start "Frontend - Vite" cmd /k "cd /d %~dp0frontend && pnpm dev"

echo.
echo ========================================
echo   Servicios iniciados correctamente
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Frontend: http://localhost:5173
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause > nul
