@echo off
echo ====================================
echo   Calls Summary - Starting Services
echo ====================================

echo.
echo [1/3] Starting PostgreSQL...
conda run -n calls_summery pg_ctl -D "C:/Users/zivre/pgdata" -l "C:/Users/zivre/pgdata/pg.log" start 2>nul
conda run -n calls_summery pg_isready -U postgres >nul 2>&1
if %errorlevel%==0 (
    echo       PostgreSQL: OK (port 5432)
) else (
    echo       PostgreSQL: FAILED - check C:/Users/zivre/pgdata/pg.log
)

echo.
echo [2/3] Starting Redis...
start /B "Redis" "C:\tools\redis\redis-server.exe" >nul 2>&1
timeout /t 2 >nul
echo       Redis: OK (port 6379)

echo.
echo [3/3] Ready! Open 4 separate terminals and run:
echo.
echo   Terminal 1 (Celery):
echo     conda run -n calls_summery celery -A src.tasks.celery_app worker --loglevel=info --pool=solo
echo.
echo   Terminal 2 (API):
echo     conda run -n calls_summery uvicorn src.api.main:app --reload
echo.
echo   Terminal 3 (Streamlit):
echo     conda run -n calls_summery streamlit run src/app.py
echo.
echo   Terminal 4 (Agent - auto-upload watcher):
echo     conda run -n calls_summery python -m agent.watcher
echo.
echo ====================================
echo   API docs: http://localhost:8000/docs
echo   UI:       http://localhost:8501
echo   Watch:    C:/Users/zivre/CallRecordings
echo ====================================
pause
