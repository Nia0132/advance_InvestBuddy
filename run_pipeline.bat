@echo off
echo ========================================================
echo Menjalankan Daily Batch ML Pipeline InvestBuddy
echo ========================================================
call .\venv\Scripts\activate.bat
python scripts/daily_pipeline.py
pause
