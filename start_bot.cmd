@echo off
setlocal EnableDelayedExpansion

echo ==============================================
echo   Sanmati Admission Bot - Startup Script
echo ==============================================
echo.

echo [1/2] Starting FastAPI Backend on Port 8000...
start /b cmd /c ".\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 > server.log 2>&1"

echo [2/2] Starting Cloudflare Tunnel...
start /b cmd /c ".\cloudflared.exe tunnel --url http://127.0.0.1:8000 > cloudflared.log 2>&1"

echo Waiting 8 seconds for the tunnel to connect...
timeout /t 8 >nul

echo.
echo ==============================================
echo BOT IS RUNNING!
echo ==============================================
echo Your permanent Cloudflare URL is:

powershell -Command "$url = (Get-Content cloudflared.log | Select-String 'https://.*trycloudflare\.com').Matches.Value | Select-Object -Last 1; Write-Host $url -ForegroundColor Green; Set-Clipboard -Value $url"

echo.
echo IMPORTANT: If the URL changes, you MUST update your Meta Webhook to:
echo ^<YOUR_URL^>/webhook
echo.
echo (The URL has been copied to your clipboard!)
echo.
echo Press any key to stop the bot and exit...
pause >nul

echo Stopping services...
taskkill /F /IM cloudflared.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
echo Done!
