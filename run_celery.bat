@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
conda run -n calls_summery celery -A src.tasks.celery_app worker --loglevel=info --pool=solo
