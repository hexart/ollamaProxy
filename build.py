#!/usr/bin/env python3
"""
跨平台客户端打包脚本
根据运行平台自动选择合适的打包方式
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def install_requirements():
    """安装打包所需的依赖"""
    print("正在安装打包依赖...")
    try:
        # 使用当前Python环境的pip安装依赖
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pystray", "Pillow", "uvicorn[standard]", "fastapi", "httpx"])
        print("依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        return False

def build_app():
    """构建跨平台应用"""
    print("开始构建跨平台应用...")
    
    # 使用PyInstaller打包
    try:
        print("正在打包应用...")
        pyinstaller_cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name", "OllamaProxy",
            "--windowed",  # 隐藏控制台窗口
            "--hidden-import", "pystray",
            "--hidden-import", "PIL",
            "--hidden-import", "fastapi",
            "--hidden-import", "uvicorn",
            "--hidden-import", "uvicorn.protocols.http.h11_impl",
            "--hidden-import", "uvicorn.protocols.websockets.wsproto_impl",
            "--hidden-import", "httpx",
            "--hidden-import", "h11",
            "--hidden-import", "click",
            "app.py"
        ]
        
        # 根据平台添加图标和资源文件
        if platform.system() == "Darwin":  # macOS
            # 添加应用图标
            pyinstaller_cmd.extend(["--icon", "resources/mac.icns"])
            # 添加托盘图标和配置文件作为数据文件
            pyinstaller_cmd.extend([
                "--add-data", "main.py:.",
                "--add-data", "config.py:.",
                "--add-data", "config.json:.",
                "--add-data", "resources/menuicon_16.png:.",
                "--add-data", "resources/menuicon_32.png:."
            ])
            # 添加额外的BUNDLE配置
            pyinstaller_cmd.extend([
                "--osx-bundle-identifier", "com.ollama.proxy",
                "--target-architecture", "arm64"
            ])
        else:  # Windows
            pyinstaller_cmd.extend(["--icon", "resources/wintray.ico"])
            # 添加托盘图标和配置文件作为数据文件
            pyinstaller_cmd.extend([
                "--add-data", "main.py;.",
                "--add-data", "config.py;.",
                "--add-data", "config.json;.",
                "--add-data", "resources/wintray.ico;."
            ])
        
        subprocess.check_call(pyinstaller_cmd)
        print("应用打包完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"应用打包失败: {e}")
        return False

def create_app_structure():
    """创建应用目录结构"""
    # 确保必要的文件存在
    required_files = ['app.py', 'main.py', 'config.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"错误: 缺少必要的文件 {file}")
            return False
    
    # 创建config.json（如果不存在）
    if not os.path.exists('config.json'):
        with open('config.json', 'w', encoding='utf-8') as f:
            f.write('{"port": 8000, "ollama_base_url": "http://localhost:11434", "timeout": 60.0}')
    
    return True

def create_platform_scripts():
    """创建平台特定的脚本"""
    if platform.system() != "Darwin":  # 非macOS平台（主要是Windows）
        # Windows服务脚本
        service_script = '''@echo off
REM Ollama Proxy Windows Service Script

REM 设置工作目录
cd /d "%~dp0"

REM 启动应用
start "" "OllamaProxy.exe"

REM 提示信息
echo Ollama Proxy service started
echo 确保Ollama服务已在运行
pause
'''
        
        with open('start_service.bat', 'w', encoding='utf-8') as f:
            f.write(service_script)
        
        # 创建安装为系统服务的脚本
        install_script = '''@echo off
REM 将Ollama Proxy安装为Windows服务的脚本
REM 需要管理员权限运行

REM 这里可以使用NSSM (Non-Sucking Service Manager) 或其他工具来创建Windows服务
echo 请使用NSSM工具将OllamaProxy.exe安装为Windows服务
echo 下载NSSM: https://nssm.cc/download
echo 使用方法: nssm install OllamaProxy "完整路径\\到\\OllamaProxy.exe"
pause
'''
        
        with open('install_service.bat', 'w', encoding='utf-8') as f:
            f.write(install_script)
        
        print("已创建Windows服务脚本")

def main():
    """主函数"""
    print("Ollama Proxy 跨平台客户端打包工具")
    print("=" * 40)
    
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"工作目录: {script_dir}")
    
    # 安装依赖
    if not install_requirements():
        return
    
    # 创建应用结构
    if not create_app_structure():
        return
    
    # 创建平台特定脚本
    create_platform_scripts()
    
    # 构建应用
    success = build_app()
    if success:
        if platform.system() == "Darwin":  # macOS
            print("\nmacOS应用打包完成!")
            print("应用位置: dist/OllamaProxy.app")
            print("\n使用说明:")
            print("1. 将 OllamaProxy.app 拖拽到 Applications 文件夹")
            print("2. 首次运行可能需要在系统偏好设置中授予权限")
            print("3. 确保Ollama服务已在运行")
        else:  # Windows 或其他平台
            print("\n应用打包完成!")
            print("应用位置: dist/OllamaProxy/")
            print("\n使用说明:")
            print("1. 将整个OllamaProxy文件夹复制到您希望安装的位置")
            print("2. 双击OllamaProxy.exe启动应用")
            print("3. 确保Ollama服务已在运行")
        
        print("\n构建成功完成!")
    else:
        print("\n构建失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()