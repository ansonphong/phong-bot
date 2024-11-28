@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python phong-bot.py
pause
deactivate
