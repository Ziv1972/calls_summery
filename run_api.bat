@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
conda run -n calls_summery uvicorn src.api.main:app --reload --port 8001
