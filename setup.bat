@echo off
setlocal EnableDelayedExpansion

echo Checking and installing prerequisites...

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check for Go
go version >nul 2>&1
if %errorlevel% neq 0 (
    echo Go not found. Please install Go from https://golang.org/dl/
    pause
    exit /b 1
)

:: Install FFmpeg using winget
winget list FFmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing FFmpeg...
    winget install FFmpeg
)

:: Ask about existing NGINX installation
set /p CUSTOM_NGINX="Do you have an existing NGINX installation that you want to manage yourself? (y/n): "
if /i "!CUSTOM_NGINX!"=="y" (
    echo Skipping NGINX installation and configuration...
    goto SKIP_NGINX
)

:: Create temp directory
if not exist "temp" mkdir temp

:: Download and extract NGINX-RTMP
echo Downloading NGINX-RTMP...
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/illuspas/nginx-rtmp-win32/archive/refs/tags/v1.2.1.zip' -OutFile 'temp\nginx-rtmp.zip'}"
powershell -Command "& {Expand-Archive -Path 'temp\nginx-rtmp.zip' -DestinationPath 'temp' -Force}"

:: Move NGINX to proper location
if exist "nginx" rd /s /q "nginx"
move "temp\nginx-rtmp-win32-1.2.1" "nginx"

:: Get stream URLs from user
set /p TWITCH_URL="Enter Twitch URL (or press Enter to skip): "
set /p YOUTUBE_URL="Enter YouTube URL for landscape (or press Enter to skip): "
set /p YOUTUBE_PORTRAIT_URL="Enter YouTube URL for portrait (or press Enter to skip): "

:: Create NGINX configuration
echo Creating NGINX configuration...
(
echo worker_processes  1;
echo events {
echo     worker_connections  1024;
echo }
echo.
echo rtmp {
echo     server {
echo         listen 1935;
echo         chunk_size 4096;
echo.
echo         application landscape {
echo             live on;
echo             record off;
) > nginx\conf\nginx.conf

:: Add Twitch push if URL provided
if not "!TWITCH_URL!"=="" (
    echo             push !TWITCH_URL!; >> nginx\conf\nginx.conf
)

:: Add YouTube landscape push if URL provided
if not "!YOUTUBE_URL!"=="" (
    echo             push !YOUTUBE_URL!; >> nginx\conf\nginx.conf
)

:: Continue configuration
(
echo         }
echo.
echo         application portrait {
echo             live on;
echo             record off;
) >> nginx\conf\nginx.conf

:: Add YouTube portrait push if URL provided
if not "!YOUTUBE_PORTRAIT_URL!"=="" (
    echo             push !YOUTUBE_PORTRAIT_URL!; >> nginx\conf\nginx.conf
)

:: Finish configuration
(
echo         }
echo     }
echo }
echo.
echo http {
echo     server {
echo         listen      80;
echo         server_name localhost;
echo     }
echo }
) >> nginx\conf\nginx.conf

:: Install Python requirements
echo Installing Python requirements...
pip install -r requirements.txt

:: Create startup task for NGINX
echo Creating NGINX startup task...
set "NGINX_PATH=%CD%\nginx\nginx.exe"
:: Create the task with full path and error handling
schtasks /Create /TN "NGINX-RTMP" /TR "'%NGINX_PATH%'" /SC ONLOGON /RL HIGHEST /F
if %errorlevel% neq 0 (
    echo Warning: Failed to create startup task. NGINX will need to be started manually.
    echo You can run: %NGINX_PATH%
) else (
    echo Successfully created NGINX startup task
)

:: Start NGINX
echo Starting NGINX...
start /B "%NGINX_PATH%"

:: Clean up temp directory
rd /s /q temp

:SKIP_NGINX
echo Setup complete!
if /i not "!CUSTOM_NGINX!"=="y" (
    echo NGINX-RTMP server is running.
    echo Portrait stream endpoint: rtmp://localhost:1935/portrait
    echo Landscape stream endpoint: rtmp://localhost:1935/landscape
)
echo Portrait stream endpoint: rtmp://localhost:1935/portrait
echo Landscape stream endpoint: rtmp://localhost:1935/landscape

echo Installing Kick bypass...
python -m kick bypass create
python -m kick bypass install

pause
