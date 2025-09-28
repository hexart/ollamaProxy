@echo off
REM Ollama Proxy Build Script (Windows)
REM Automatically creates virtual environment, activates it, and builds the application

echo [INFO] Ollama Proxy Build Script (Windows)
echo ========================

REM Get script directory
set SCRIPT_DIR=%~dp0
echo [INFO] Working directory: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists, if not create it
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        exit /b 1
    )
    echo [INFO] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    exit /b 1
)

REM Install requirements
echo [INFO] Installing requirements from requirements.txt...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install requirements
        exit /b 1
    )
    echo [INFO] Requirements installed
) else (
    echo [WARNING] requirements.txt not found, skipping...
)

REM Install build dependencies
echo [INFO] Installing build dependencies...
pip install pyinstaller pystray Pillow uvicorn[standard] fastapi httpx
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install build dependencies
    exit /b 1
)
echo [INFO] Build dependencies installed

REM Kill any running processes that might be locking the dist directory
echo [INFO] Checking for processes that might be locking the dist directory...
taskkill /f /im OllamaProxy.exe >nul 2>nul

REM Wait a moment for processes to terminate
timeout /t 2 /nobreak >nul

REM Build application with pyinstaller
echo [INFO] Building application with pyinstaller...
python -m PyInstaller --noconfirm --name=OllamaProxy --windowed --icon=resources/wintray.ico --add-data="resources;resources" --hidden-import=pystray --hidden-import=PIL --add-data="main.py;." --add-data="config.py;." --add-data="config.json;." --add-data="resources/wintray.ico;." app.py
if %errorlevel% neq 0 (
    echo [ERROR] Application build failed
    exit /b 1
)
echo [INFO] Application built successfully

REM Create ZIP package
echo [INFO] Creating ZIP package...
if exist "dist\OllamaProxy\" (
    cd dist
    if exist "OllamaProxy.zip" (
        del "OllamaProxy.zip"
    )
    
    REM Wait a bit to ensure PyInstaller has fully released all file locks
    timeout /t 3 /nobreak >nul
    
    REM Retry mechanism for creating ZIP package
    set retry_count=0
    :retry_zip
    echo [INFO] Attempting to create ZIP package (attempt %retry_count%)
    
    REM Use PowerShell to create ZIP (works on Windows 10+)
    powershell -Command "Compress-Archive -Path 'OllamaProxy\*' -DestinationPath 'OllamaProxy.zip' -Force"
    if %errorlevel% equ 0 (
        echo [INFO] ZIP package created: dist\OllamaProxy.zip
        REM Get ZIP file size
        for %%I in ("OllamaProxy.zip") do (
            echo [INFO] ZIP file size: %%~zI bytes
        )
    ) else (
        set /a retry_count+=1
        if %retry_count% LSS 3 (
            echo [WARNING] Failed to create ZIP package, waiting 2 seconds before retry...
            timeout /t 2 /nobreak >nul
            goto :retry_zip
        ) else (
            echo [ERROR] Failed to create ZIP package after 3 attempts
            cd ..
            exit /b 1
        )
    )
    cd ..
) else (
    echo [ERROR] OllamaProxy directory not found in dist
)

echo [INFO] Build completed successfully!
echo [INFO] Application location: dist\OllamaProxy\
if exist "dist\OllamaProxy.zip" (
    echo [INFO] ZIP package: dist\OllamaProxy.zip
)