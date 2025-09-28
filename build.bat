@echo off
REM Ollama Proxy Build Script (Windows)
REM Using uv to create virtual environment and build application

echo [INFO] Ollama Proxy Build Script (Windows)
echo ========================

REM Get script directory
set SCRIPT_DIR=%~dp0
echo [INFO] Working directory: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"

REM Check if uv is installed, install if not
python -m uv --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] uv not detected, installing...
    python -m pip install uv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install uv, please ensure Python and pip are installed
        exit /b 1
    )
    echo [INFO] uv installation completed
)

REM Check if uv is available
python -m uv --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] uv is not available, please add it to system PATH manually
    exit /b 1
)

echo [INFO] Detected uv version:
for /f "delims=" %%i in ('python -m uv --version') do echo [INFO] %%i

REM Check if virtual environment exists
if exist ".venv" (
    echo [INFO] Existing virtual environment detected
) else (
    echo [INFO] No virtual environment detected, creating...
    python -m uv venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        exit /b 1
    )
    echo [INFO] Virtual environment created
)

REM Install requirements in virtual environment using system uv
echo [INFO] Installing requirements...
python -m uv pip install -r requirements.txt --python .venv\Scripts\python.exe
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements
    exit /b 1
)
echo [INFO] Requirements installation completed

REM Install build dependencies using system uv
echo [INFO] Installing build dependencies...
python -m uv pip install pyinstaller pystray Pillow uvicorn[standard] fastapi httpx --python .venv\Scripts\python.exe
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install build dependencies
    exit /b 1
)
echo [INFO] Build dependencies installation completed

REM Build application using uv run with system python
echo [INFO] Building application with uv run...
python -m uv run --python .venv\Scripts\python.exe build.py
if %errorlevel% neq 0 (
    echo [ERROR] Application build failed
    exit /b 1
)
echo [INFO] Application build completed

echo [INFO] Build completed successfully!
echo [INFO] Application location: dist\OllamaProxy\

pause