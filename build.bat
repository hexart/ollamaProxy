@echo off
REM Ollama Proxy 构建脚本 (Windows版本)
REM 使用uv创建虚拟环境并构建应用

SETLOCAL EnableDelayedExpansion

echo [INFO] Ollama Proxy 构建脚本 (Windows版本)
echo ========================

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
echo [INFO] 工作目录: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"

REM 检查uv是否已安装
where uv >nul 2>nul
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('uv --version') do set UV_VERSION=%%i
    echo [INFO] 检测到uv: %UV_VERSION%
) else (
    echo [WARNING] 未检测到uv，正在安装...
    python -m pip install uv
    if !errorlevel! neq 0 (
        echo [ERROR] uv安装失败，请确保已安装Python和pip
        exit /b 1
    )
    echo [INFO] uv安装完成
)

REM 检查虚拟环境是否存在
if exist ".venv" (
    echo [INFO] 检测到现有虚拟环境
) else (
    echo [INFO] 未检测到虚拟环境，正在创建...
    uv venv .venv
    if !errorlevel! neq 0 (
        echo [ERROR] 虚拟环境创建失败
        exit /b 1
    )
    echo [INFO] 虚拟环境创建完成
)

REM 激活虚拟环境
echo [INFO] 正在激活虚拟环境...
call .venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo [ERROR] 虚拟环境激活失败
    exit /b 1
)
echo [INFO] 虚拟环境已激活: %PYTHON_PATH%

REM 安装依赖
echo [INFO] 正在安装依赖...
uv pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] 依赖安装失败
    exit /b 1
)
echo [INFO] 依赖安装完成

REM 构建应用
echo [INFO] 正在构建应用...
python build.py
if !errorlevel! neq 0 (
    echo [ERROR] 应用构建失败
    exit /b 1
)
echo [INFO] 应用构建完成

echo [INFO] 🎉 构建完成!
echo [INFO] 应用位置: dist\OllamaProxy\

pause