#!/bin/bash

# Ollama Proxy 构建脚本
# 使用uv创建虚拟环境并构建应用

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查uv是否已安装
check_uv() {
    if command -v uv &> /dev/null; then
        print_info "检测到uv: $(uv --version)"
        return 0
    else
        print_warning "未检测到uv"
        return 1
    fi
}

# 安装uv
install_uv() {
    print_info "正在安装uv..."
    if command -v pip &> /dev/null; then
        pip install uv
        print_info "uv安装完成"
    else
        print_error "未找到pip，请先安装Python和pip"
        exit 1
    fi
}

# 创建虚拟环境
create_venv() {
    print_info "正在创建虚拟环境..."
    uv venv .venv
    print_info "虚拟环境创建完成"
}

# 激活虚拟环境
activate_venv() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        source .venv/Scripts/activate
    else
        # macOS/Linux
        source .venv/bin/activate
    fi
    print_info "虚拟环境已激活: $(which python)"
}

# 安装依赖
install_dependencies() {
    print_info "正在安装依赖..."
    uv pip install -r requirements.txt
    print_info "依赖安装完成"
}

# 构建应用
build_app() {
    print_info "正在构建应用..."
    python build.py
    print_info "应用构建完成"
}

# 主函数
main() {
    print_info "Ollama Proxy 构建脚本"
    print_info "========================"
    
    # 获取脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    print_info "工作目录: $SCRIPT_DIR"
    
    # 切换到脚本所在目录
    cd "$SCRIPT_DIR"
    
    # 检查uv是否已安装
    if ! check_uv; then
        install_uv
    fi
    
    # 检查虚拟环境是否存在
    if [ -d ".venv" ]; then
        print_info "检测到现有虚拟环境"
    else
        print_info "未检测到虚拟环境，正在创建..."
        create_venv
    fi
    
    # 激活虚拟环境
    activate_venv
    
    # 安装依赖
    install_dependencies
    
    # 构建应用
    build_app
    
    print_info "🎉 构建完成!"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "应用位置: dist/OllamaProxy.app"
    else
        print_info "应用位置: dist/OllamaProxy/"
    fi
}

# 运行主函数
main "$@"