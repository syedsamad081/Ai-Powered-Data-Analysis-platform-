@echo off
title AI Data Platform

echo ============================================
echo   AI Data Platform - Final Year Project
echo ============================================
echo.

REM Check if .env exists, warn if not
if not exist ".env" (
    echo WARNING: No .env file found.
    echo Please copy .env.example to .env and add your Gemini API key.
    echo.
    pause
)

REM Install / update dependencies silently
echo Installing dependencies...
pip install -q -r requirements.txt
echo Done.
echo.

REM Start the Flask server
echo Starting server...
echo Open your browser at: http://localhost:5000
echo Press Ctrl+C to stop the server.
echo.

python app.py

pause
