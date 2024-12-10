@echo on
setlocal EnableDelayedExpansion

echo Starting setup script...
echo Current directory: %CD%
echo.

echo Checking and installing prerequisites...
pause

:: Check for winget by running version command
echo Checking for winget...
winget --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Winget is already installed:
    winget --version
    echo.
    echo Continuing with setup...
) else (
    echo Winget not found. Please install App Installer from the Microsoft Store
    echo Visit: https://www.microsoft.com/store/productId/9NBLGGH4NNS1
    echo After installation, please restart this script
    pause
    exit /b 1
)

:: Check for curl by looking in common locations
echo Checking for curl...
where curl >nul 2>nul
if %errorlevel% equ 0 (
    echo Curl is already installed:
    curl --version
    echo.
    echo Continuing with setup...
    for /f "delims=" %%i in ('where curl') do set "CURL_PATH=%%i"
) else (
    echo Curl not found. Installing curl...
    winget install cURL.cURL --accept-source-agreements --accept-package-agreements --silent
    if %errorlevel% neq 0 (
        echo Failed to install curl. Please install curl manually.
        echo Visit: https://curl.se/windows/
        pause
        exit /b 1
    )

    :: Wait for installation to complete
    timeout /t 5 /nobreak

    :: Get the new PATH from the registry and set it for current session
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "PATH=%%b"
    for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "PATH=!PATH!;%%b"

    :: Check common locations for curl
    if exist "C:\Windows\System32\curl.exe" (
        set "CURL_PATH=C:\Windows\System32\curl.exe"
    ) else if exist "C:\Program Files\curl\bin\curl.exe" (
        set "CURL_PATH=C:\Program Files\curl\bin\curl.exe"
    ) else if exist "C:\Program Files (x86)\curl\bin\curl.exe" (
        set "CURL_PATH=C:\Program Files (x86)\curl\bin\curl.exe"
    ) else (
        echo Could not find curl.exe in common locations.
        echo Please restart your computer and run setup again.
        pause
        exit /b 1
    )
    echo Found curl at: !CURL_PATH!
    echo Curl installed successfully!
)

:: Set CURL_PATH if not already set
if not defined CURL_PATH (
    for /f "delims=" %%i in ('where curl') do set "CURL_PATH=%%i"
)

goto :StartSetup

:AddToPath
setlocal EnableDelayedExpansion
set "PathToAdd=%~1"
:: Add to PATH if not already present
echo %PATH% | find /i "%PathToAdd%" >nul || setx /M PATH "%PATH%;%PathToAdd%"
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
:: Refresh PATH from registry
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "PATH=%%b"

:: Ask about existing NGINX installation
set /p CUSTOM_NGINX="Do you have an existing NGINX installation that you want to manage yourself? (y/n): "
if /i "!CUSTOM_NGINX!"=="y" (
    echo Skipping NGINX installation and configuration...
    goto SKIP_NGINX
)

echo.
echo Starting NGINX installation...
echo Current directory: %CD%

:: Create temp directory
if not exist "temp" mkdir temp
echo Created temp directory at: %CD%\temp

:: Download NGINX-RTMP using curl
echo Downloading NGINX-RTMP...
"%CURL_PATH%" -L -o temp\nginx-rtmp.zip https://github.com/illuspas/nginx-rtmp-win32/archive/refs/tags/v1.2.1.zip
if not exist "temp\nginx-rtmp.zip" (
    echo Failed to download NGINX-RTMP
    pause
    exit /b 1
)
echo Successfully downloaded NGINX-RTMP to: %CD%\temp\nginx-rtmp.zip

:: Extract NGINX-RTMP using tar (built into Windows 10+)
echo Extracting NGINX-RTMP...
tar -xf temp\nginx-rtmp.zip -C temp
if not exist "temp\nginx-rtmp-win32-1.2.1" (
    echo Failed to extract NGINX-RTMP
    pause
    exit /b 1
)
echo Successfully extracted NGINX-RTMP to: %CD%\temp\nginx-rtmp-win32-1.2.1

:: Move NGINX to proper location
echo Moving NGINX to final location...
if exist "nginx" (
    echo Removing existing NGINX directory...
    rd /s /q "nginx"
)
move "temp\nginx-rtmp-win32-1.2.1" "nginx"
if not exist "nginx\nginx.exe" (
    echo Failed to properly install NGINX. nginx.exe not found.
    echo Expected location: %CD%\nginx\nginx.exe
    pause
    exit /b 1
)
echo Successfully installed NGINX to: %CD%\nginx

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
echo.
echo Starting NGINX...
echo NGINX Path: %NGINX_PATH%

if not exist "%NGINX_PATH%" (
    echo ERROR: NGINX executable not found at: %NGINX_PATH%
    pause
    exit /b 1
)

:: Kill any existing NGINX process
taskkill /F /IM nginx.exe /T >nul 2>&1

:: Start NGINX with output
"%NGINX_PATH%"
if %errorlevel% neq 0 (
    echo Failed to start NGINX
    pause
    exit /b 1
)

:: Verify NGINX is running
timeout /t 2 /nobreak >nul
tasklist | find "nginx.exe" >nul
if %errorlevel% neq 0 (
    echo ERROR: NGINX failed to start
    pause
    exit /b 1
)
echo NGINX started successfully!

:: Clean up temp directory
echo.
echo Cleaning up temporary files...
rd /s /q temp
echo Cleanup complete!

:: Display NGINX installation information
echo.
echo NGINX Installation Summary:
echo -------------------------
echo Executable: %NGINX_PATH%
echo Config file: %CD%\nginx\conf\nginx.conf
echo Logs directory: %CD%\nginx\logs
echo.

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
