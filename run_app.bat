@echo off
echo ========================================================
echo Memulai InvestBuddy Web Server (InvestBot v2.0)
echo ========================================================
call .\venv\Scripts\activate.bat
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
pause
