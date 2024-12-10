@echo on
setlocal EnableDelayedExpansion

echo Starting setup script...
echo Current directory: %CD%
echo.

echo Checking and installing prerequisites...
pause

:: Check for winget using PowerShell
echo Checking for winget...
powershell -Command "& { if (Get-Command winget -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 } }"
if %errorlevel% equ 0 (
    echo Winget is already installed, continuing...
    pause
) else (
    echo Winget not found. Attempting to install...

    :: Create temp directory for winget installation
    if not exist "temp" mkdir temp
    cd temp

    :: Download latest Microsoft.DesktopAppInstaller from GitHub
    echo Downloading App Installer...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://aka.ms/getwinget' -OutFile 'Microsoft.DesktopAppInstaller.msixbundle'}"

    :: Install using PowerShell Add-AppxPackage
    echo Installing App Installer...
    powershell -Command "& {Add-AppxPackage -Path '.\Microsoft.DesktopAppInstaller.msixbundle'}"

    :: Clean up
    cd ..
    rd /s /q temp

    :: Verify installation
    powershell -Command "& { if (Get-Command winget -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 } }"
    if %errorlevel% neq 0 (
        echo Error: Failed to install winget. Please install manually from the Microsoft Store.
        echo.
        echo Script completed with errorlevel: %errorlevel%
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo Winget installed successfully!
    pause
)

:: Add debug pause to see if we get past winget check
echo Proceeding past winget check...
pause

:: Function to permanently add to PATH
:AddToPath
setlocal EnableDelayedExpansion
set "PathToAdd=%~1"
:: Check if path already exists in system PATH
powershell -Command "& {$newPath='%PathToAdd%'; $currentPath=[Environment]::GetEnvironmentVariable('PATH', 'Machine'); if ($currentPath -notlike '*' + $newPath + '*') {[Environment]::SetEnvironmentVariable('PATH', $currentPath + ';' + $newPath, 'Machine')}}"
endlocal
goto :eof

:: Check/Install Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Installing Python...
    winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements
    :: Update PATH for this session and permanently
    set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python311"
    set "PYTHON_SCRIPTS=%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
    set "PATH=%PATH%;%PYTHON_PATH%;%PYTHON_SCRIPTS%"
    call :AddToPath "%PYTHON_PATH%"
    call :AddToPath "%PYTHON_SCRIPTS%"
)

:: Check/Install Go
go version >nul 2>&1
if %errorlevel% neq 0 (
    echo Go not found. Installing Go...
    winget install GoLang.Go --accept-source-agreements --accept-package-agreements
    :: Update PATH for this session and permanently
    set "GO_PATH=%PROGRAMFILES%\Go\bin"
    set "PATH=%PATH%;%GO_PATH%"
    call :AddToPath "%GO_PATH%"
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
