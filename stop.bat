@echo off
echo Stopping services...
conda run -n calls_summery pg_ctl -D "C:/Users/zivre/pgdata" stop 2>nul
taskkill /IM redis-server.exe /F 2>nul
echo Done.
