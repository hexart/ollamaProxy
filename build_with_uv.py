#!/usr/bin/env python3
"""
使用uv创建虚拟环境并打包应用的脚本
"""

import os
import sys
import subprocess
import platform

def check_uv_installed():
    """检查uv是否已安装"""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_uv():
    """安装uv"""
    print("正在安装uv...")
    try:
        # 在macOS/Linux上使用pip安装
        if platform.system() != "Windows":
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
        else:
            # 在Windows上也使用pip安装
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
        print("uv安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"uv安装失败: {e}")
        return False

def create_venv_with_uv():
    """使用uv创建虚拟环境并安装依赖"""
    print("正在使用uv创建虚拟环境...")
    try:
        # 创建虚拟环境
        subprocess.run(["uv", "venv", ".venv"], check=True)
        print("虚拟环境创建完成")
        
        # 激活虚拟环境并安装依赖
        if platform.system() == "Windows":
            activate_script = os.path.join(".venv", "Scripts", "activate")
            pip_cmd = os.path.join(".venv", "Scripts", "pip")
        else:
            activate_script = os.path.join(".venv", "bin", "activate")
            pip_cmd = os.path.join(".venv", "bin", "pip")
        
        # 安装依赖
        subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], check=True)
        print("依赖安装完成")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"虚拟环境创建或依赖安装失败: {e}")
        return False

def build_app_in_venv():
    """在虚拟环境中构建应用"""
    print("正在虚拟环境中构建应用...")
    try:
        # 构建应用
        if platform.system() == "Windows":
            python_cmd = os.path.join(".venv", "Scripts", "python")
        else:
            python_cmd = os.path.join(".venv", "bin", "python")
        
        subprocess.run([python_cmd, "build.py"], check=True)
        print("应用构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"应用构建失败: {e}")
        return False

def main():
    """主函数"""
    print("Ollama Proxy 打包工具 (使用uv创建虚拟环境)")
    print("=" * 50)
    
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"工作目录: {script_dir}")
    
    # 检查uv是否已安装
    if not check_uv_installed():
        print("未检测到uv，正在安装...")
        if not install_uv():
            print("uv安装失败，退出")
            return False
    
    # 创建虚拟环境并安装依赖
    if not create_venv_with_uv():
        print("虚拟环境创建失败，退出")
        return False
    
    # 在虚拟环境中构建应用
    if not build_app_in_venv():
        print("应用构建失败")
        return False
    
    print("\n🎉 打包完成!")
    if platform.system() == "Darwin":  # macOS
        print("应用位置: dist/OllamaProxy.app")
    else:  # Windows 或其他平台
        print("应用位置: dist/OllamaProxy/")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)