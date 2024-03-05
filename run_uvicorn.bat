@echo off
:restart
echo "Starting Uvicorn..."
uvicorn main:app --host 0.0.0.0 --port 8000
echo "Uvicorn crashed... restarting in 5 seconds."
timeout /t 5
goto restart