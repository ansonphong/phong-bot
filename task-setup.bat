@echo off
:: This script creates a scheduled task for the bot
:: Usage: task-setup.bat [frequency]
:: frequency can be: daily, weekly, or custom (defaults to M/W/F at 7am)

set TASK_NAME=PhongBot
set SCRIPT_PATH=%~dp0run-bot.bat

if "%1"=="" (
    :: Default schedule (Monday, Wednesday, Friday at 7am)
    schtasks /create /tn "%TASK_NAME%" /tr "%SCRIPT_PATH%" /sc weekly /d MON,WED,FRI /st 07:00 /f
) else if "%1"=="daily" (
    schtasks /create /tn "%TASK_NAME%" /tr "%SCRIPT_PATH%" /sc daily /st 07:00 /f
) else if "%1"=="weekly" (
    schtasks /create /tn "%TASK_NAME%" /tr "%SCRIPT_PATH%" /sc weekly /d MON /st 07:00 /f
) else if "%1"=="custom" (
    :: You can modify this to add custom scheduling options
    echo Please edit task-setup.bat to add your custom schedule
) else (
    echo Invalid frequency specified
    echo Usage: task-setup.bat [frequency]
    echo Frequencies: daily, weekly, custom
    exit /b 1
)

echo Task scheduled successfully