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

goto :StartSetup

:AddToPath
setlocal EnableDelayedExpansion
set "PathToAdd=%~1"
:: Check if path already exists in system PATH
powershell -Command "& {$newPath='%PathToAdd%'; $currentPath=[Environment]::GetEnvironmentVariable('PATH', 'Machine'); if ($currentPath -notlike '*' + $newPath + '*') {[Environment]::SetEnvironmentVariable('PATH', $currentPath + ';' + $newPath, 'Machine')}}"
endlocal
goto :AddToPath_Return

:AddToPath_Return

:StartSetup

:: Check/Install Python
echo Checking for Python 3...
python --version 2>nul | find "3." >nul
if %errorlevel% equ 0 (
    echo Python 3.11 is already installed.
    goto PYTHON_INSTALLED
)

echo Python 3.11 not found. Installing Python...
    winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements --silent
    if %errorlevel% neq 0 (
        echo Failed to install Python via winget. Please install Python 3.11 manually.
        echo Visit: https://www.python.org/downloads/
        pause
        exit /b 1
    )

    :: Wait for installation to complete and verify
    timeout /t 5 /nobreak

    :: Refresh PATH
    set "RETURN_LABEL=After_Python_Path"
    call :RefreshPath
    :After_Python_Path

    :: Verify Python installation
    python --version 2>nul | find "3.11" >nul
    if %errorlevel% neq 0 (
        echo Python installation completed but version check failed.
        echo Please restart your computer and run setup again.
        echo Current Python version:
        python --version
        pause
        exit /b 1
    )
    echo Python 3.11 installed successfully!
)

:PYTHON_INSTALLED

:: Check/Install Go
echo Checking for Go...
go version >nul 2>&1
if %errorlevel% equ 0 (
    echo Go is already installed:
    go version
    goto GO_INSTALLED
)
    echo Go not found. Installing Go...
    winget install GoLang.Go --accept-source-agreements --accept-package-agreements --silent
    if %errorlevel% neq 0 (
        echo Failed to install Go. Please install Go manually.
        echo Visit: https://golang.org/dl/
        pause
        exit /b 1
    )

    :: Wait for installation to complete
    timeout /t 5 /nobreak

    :: Refresh PATH
    call :RefreshPath

    :: Verify Go installation
    powershell -Command "& { if (Get-Command go -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 } }"
    if %errorlevel% neq 0 (
        echo Go installation failed or PATH not updated. Please restart your computer and run setup again.
        pause
        exit /b 1
    )
    echo Go installed successfully!
)

:GO_INSTALLED

:: Check/Install FFmpeg
echo Checking for FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo FFmpeg is already installed:
    ffmpeg -version
    goto FFMPEG_INSTALLED
)
    echo FFmpeg not found. Installing FFmpeg...
    winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements --silent
    if %errorlevel% neq 0 (
        echo Failed to install FFmpeg. Please install FFmpeg manually.
        echo Visit: https://ffmpeg.org/download.html
        pause
        exit /b 1
    )

    :: Wait for installation to complete
    timeout /t 5 /nobreak

    :: Refresh PATH
    call :RefreshPath

    :: Verify FFmpeg installation
    powershell -Command "& { if (Get-Command ffmpeg -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 } }"
    if %errorlevel% neq 0 (
        echo FFmpeg installation failed or PATH not updated. Please restart your computer and run setup again.
        pause
        exit /b 1
    )
    echo FFmpeg installed successfully!
)

:FFMPEG_INSTALLED

:: Function to refresh PATH environment
:RefreshPath
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "system_path=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "user_path=%%b"
set "PATH=%system_path%;%user_path%"

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
