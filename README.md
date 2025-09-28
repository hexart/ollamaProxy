# Ollama Proxy 客户端

这是一个将Ollama API转换为OpenAI兼容格式的跨平台系统托盘应用，支持macOS和Windows系统。

## 功能特性

- 跨平台支持（macOS和Windows）
- 在系统托盘中运行，不占用桌面空间
- 自动启动Ollama代理服务
- 支持OpenAI兼容的API接口
- 支持聊天完成和文本完成接口
- 支持流式响应
- 支持CORS跨域请求
- 绿色指示器显示服务运行状态
- 可配置端口

## API端点

- `/v1/models` - 列出可用模型
- `/v1/chat/completions` - 聊天完成
- `/v1/completions` - 文本完成
- `/health` - 健康检查
- `/docs` - Swagger UI文档
- `/redoc` - ReDoc文档

## 系统要求

### macOS
- macOS 10.12或更高版本
- Python 3.7或更高版本（仅用于开发和打包）

### Windows
- Windows 7或更高版本
- Python 3.7或更高版本（仅用于开发和打包）

### 通用要求
- Ollama服务已安装并运行

## 安装

1. 确保已安装Ollama并拉取了所需模型
2. 根据您的平台选择相应的安装方式：
   - **macOS**: 下载`OllamaProxy.app`应用，将应用拖拽到Applications文件夹
   - **Windows**: 下载打包好的`OllamaProxy`应用，解压到您希望安装的位置

## 使用方法

1. 启动应用后，系统托盘会显示🦙图标
2. 服务会自动启动，绿色点表示运行中
3. 点击系统托盘图标可访问以下功能：
   - 启动服务/停止服务：手动控制服务状态
   - 端口设置：修改服务端口
   - 退出：退出应用

## 配置

应用使用`config.json`文件进行配置：

```json
{
  "port": 8000,
  "ollama_base_url": "http://localhost:11434",
  "timeout": 60.0
}
```

## 开发

### 项目结构

```
├── app.py              # 跨平台系统托盘应用主程序（使用pystray）
├── main.py             # FastAPI服务核心
├── config.py           # 配置管理
├── config.json         # 配置文件
├── build.py            # 跨平台打包脚本
├── build.sh            # macOS/Linux构建脚本（自动创建DMG）
├── build.bat           # Windows构建脚本（自动创建ZIP）
├── requirements.txt    # 依赖列表
├── resources/          # 图标资源文件夹
│   ├── mac.icns        # macOS应用图标文件
│   ├── menuicon_16.png # macOS菜单栏16x16 PNG图标文件
│   ├── menuicon_32.png # macOS菜单栏32x32 PNG图标文件
│   └── wintray.ico     # Windows系统托盘图标文件
└── README.md           # 说明文档
```

### 技术架构

本项目使用统一的跨平台架构：
- **系统托盘**: 使用 `pystray` 库实现跨平台系统托盘支持
  - macOS: 基于 PyObjC 实现
  - Windows: 基于 Win32 API 实现
  - Linux: 基于 GTK 实现
- **核心服务**: 使用 `FastAPI` 实现Ollama代理服务
- **打包工具**: 使用 `PyInstaller` 生成独立应用
- **图标分离**: 应用图标和系统托盘图标分离设计，提供更精细的视觉体验

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py
```

### 打包应用

#### 方法1：使用直接打包脚本
```bash
# 打包应用（会根据当前平台自动选择合适的打包方式）
python build.py
```

#### 方法2：使用Shell脚本打包（推荐）

**macOS/Linux:**
```bash
# 使用build.sh脚本，自动构建App并创建DMG安装包
./build.sh
```

**Windows:**
```powershell
# 使用build.bat脚本，自动构建应用并创建ZIP压缩包
.\build.bat
```

### 构建结果

**macOS:**
- `dist/OllamaProxy.app` - macOS应用程序
- `dist/OllamaProxy.dmg` - DMG安装包（自动生成）

**Windows:**
- `dist/OllamaProxy/` - Windows应用程序目录
- `dist/OllamaProxy.zip` - ZIP压缩包（自动生成）

### 构建特性

所有构建方法都会：
1. 自动检测并安装uv（如果尚未安装）
2. 创建或使用现有的虚拟环境
3. 在虚拟环境中安装所有依赖
4. 使用PyInstaller构建独立的应用程序
5. **macOS**: 自动创建美观的DMG安装包
6. **Windows**: 自动创建便于分发的ZIP压缩包

## API使用示例

### 列出模型
```bash
curl http://localhost:8000/v1/models
```

### 聊天完成
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## 故障排除

1. 如果应用无法启动，请检查Ollama服务是否正在运行
2. 如果端口冲突，请修改config.json中的端口设置
3. 如果遇到权限问题：
   - macOS: 请在系统偏好设置中授予权限
   - Windows: 请以管理员身份运行

## 许可证

MIT