#!/usr/bin/env python3
"""
跨平台系统托盘应用主程序
使用 pystray 实现跨平台系统托盘支持
- macOS: 使用 pystray (基于 PyObjC)
- Windows: 使用 pystray
- Linux: 使用 pystray (基于 GTK)
"""

import threading
import time
import requests
import os
import sys
import json
import platform

# 尝试导入main模块启动服务
try:
    from main import app as fastapi_app
    import uvicorn
    HAS_LOCAL_SERVER = True
except ImportError:
    HAS_LOCAL_SERVER = False

class CrossPlatformApp:
    def __init__(self):
        self.server_process = None
        self.server_thread = None
        self.port = self.load_port_config()
        self.is_running = False
        self.server_instance = None
        self.icon = None

        # 使用定时器延迟自动启动服务
        self.delayed_auto_start()

    def delayed_auto_start(self):
        """延迟自动启动服务"""
        # 在新线程中启动服务，避免阻塞UI
        threading.Thread(target=self.auto_start_server, daemon=True).start()

    def load_port_config(self):
        """从配置文件加载端口设置"""
        try:
            # 获取配置文件的正确路径
            if getattr(sys, 'frozen', False):
                # 打包后的应用
                config_path = os.path.join(os.getcwd(), 'config.json')
            else:
                # 开发环境
                config_path = os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), 'config.json')

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('port', 8000)
            else:
                # 创建默认配置文件
                config = {
                    "port": 8000, "ollama_base_url": "http://localhost:11434", "timeout": 60.0}
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                return 8000
        except Exception:
            return 8000

    def save_port_config(self, new_port):
        """保存端口设置到配置文件"""
        try:
            # 获取配置文件的正确路径
            if getattr(sys, 'frozen', False):
                # 打包后的应用
                config_path = os.path.join(os.getcwd(), 'config.json')
            else:
                # 开发环境
                config_path = os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), 'config.json')
            
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            config['port'] = new_port

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            self.port = new_port
            return True
        except Exception:
            return False

    def auto_start_server(self):
        """自动启动服务"""
        try:
            # 使用线程启动服务
            self.server_thread = threading.Thread(
                target=self.run_server, daemon=True)
            self.server_thread.start()

            # 多次尝试检查服务是否启动
            max_attempts = 5
            for attempt in range(max_attempts):
                time.sleep(1)
                if self.is_server_running():
                    self.is_running = True
                    # 更新菜单状态
                    if self.icon:
                        self.update_menu()
                    return

            # 如果多次尝试后仍未启动
            print("服务将在您手动启动时运行")
        except Exception:
            pass

    def is_server_running(self):
        """检查服务是否正在运行"""
        try:
            response = requests.get(
                f"http://localhost:{self.port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def start_server(self, icon=None, item=None):
        """启动FastAPI服务"""
        if self.is_running:
            return

        try:
            # 使用线程启动服务
            self.server_thread = threading.Thread(
                target=self.run_server, daemon=True)
            self.server_thread.start()

            # 等待服务启动
            time.sleep(2)

            # 检查服务是否成功启动
            if self.is_server_running():
                self.is_running = True
                # 更新菜单状态
                if icon:
                    self.update_menu(icon)
            else:
                print("无法启动服务")

        except Exception:
            pass

    def run_server(self):
        """在后台线程中运行服务器"""
        try:
            # 导入并运行FastAPI应用
            import uvicorn
            from main import app
            
            # 修复Windows打包应用中的日志配置问题
            # 当sys.stdout或sys.stderr为None时，uvicorn会出错
            if getattr(sys, 'frozen', False) and (sys.stdout is None or sys.stderr is None):
                # 在打包的Windows应用中禁用访问日志以避免isatty错误
                config = uvicorn.Config(
                    app,
                    host="127.0.0.1",  # 改为127.0.0.1以提高安全性
                    port=self.port,
                    log_level="info",
                    access_log=False,  # 禁用访问日志
                    use_colors=False    # 禁用颜色输出
                )
            else:
                config = uvicorn.Config(
                    app,
                    host="127.0.0.1",
                    port=self.port,
                    log_level="info",
                    access_log=False
                )
            
            self.server_instance = uvicorn.Server(config)
            self.server_instance.run()
        except Exception:
            pass

    def stop_server(self, icon=None, item=None):
        """停止FastAPI服务"""
        try:
            # 停止服务器
            if self.server_instance:
                self.server_instance.should_exit = True

            # 等待一段时间让服务器停止
            time.sleep(1)

            # 更新状态
            self.is_running = False
            
            # 更新菜单状态
            if icon:
                self.update_menu(icon)

        except Exception:
            pass

    def set_port(self, icon=None, item=None):
        """设置端口"""
        current_port = self.port
        
        # 根据平台选择合适的输入方式
        if platform.system() == "Darwin":  # macOS
            # 使用AppleScript创建一个简单的输入对话框
            import subprocess
            script = f'''
            display dialog "当前端口: {current_port}
请输入新端口 (1024-65535):
注意：修改端口后需要重启服务才能生效。" ¬
            default answer "{current_port}" ¬
            with title "Ollama Proxy - 端口设置" ¬
            with icon note
            
            set newPort to text returned of result
            return newPort
            '''

            try:
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    check=True
                )
                new_port = result.stdout.strip()
                
                try:
                    new_port = int(new_port)
                    if 1024 <= new_port <= 65535:
                        if self.save_port_config(new_port):
                            self.port = new_port
                    else:
                        print("端口必须在1024-65535之间。")
                except ValueError:
                    print("请输入有效的端口号。")
            except subprocess.CalledProcessError:
                # 用户取消了操作
                pass
        else:  # Windows 或其他平台
            # 在Windows上使用简单的输入对话框
            try:
                import tkinter as tk
                from tkinter import simpledialog
                
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
                
                new_port = simpledialog.askinteger(
                    "Ollama Proxy - 端口设置",
                    f"当前端口: {current_port}\n请输入新端口 (1024-65535):\n注意：修改端口后需要重启服务才能生效。",
                    initialvalue=current_port,
                    minvalue=1024,
                    maxvalue=65535
                )
                
                if new_port is not None:
                    if self.save_port_config(new_port):
                        self.port = new_port
                
                root.destroy()
                
            except Exception:
                pass

    def update_menu(self, icon=None):
        """更新托盘菜单"""
        if icon is None:
            icon = self.icon
            
        if icon:
            import pystray
            from PIL import Image, ImageDraw
            
            # 创建菜单项
            menu_items = [
                pystray.MenuItem(
                    f"服务状态: {'运行中' if self.is_running else '已停止'}",
                    lambda icon, item: None,
                    enabled=False
                ),
                pystray.MenuItem("启动服务", self.start_server,
                               enabled=not self.is_running),
                pystray.MenuItem("停止服务", self.stop_server,
                               enabled=self.is_running),
                pystray.MenuItem("设置端口", self.set_port),
                pystray.MenuItem("退出", self.quit_app)
            ]
            
            icon.menu = pystray.Menu(*menu_items)

    def quit_app(self, icon=None, item=None):
        """退出应用"""
        try:
            # 停止服务器
            if self.server_instance:
                self.server_instance.should_exit = True

            # 停止托盘图标
            if self.icon:
                self.icon.stop()
                
        except Exception:
            pass

def create_image():
    """创建托盘图标"""
    try:
        # 尝试从文件加载图标
        if platform.system() == "Darwin":  # macOS
            icon_path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "resources", "menuicon_32.png")
        else:  # Windows/Linux
            icon_path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "resources", "wintray.ico")
            
        if os.path.exists(icon_path):
            from PIL import Image
            return Image.open(icon_path)
    except Exception:
        pass
    
    # 如果无法加载图标文件，则创建一个简单的图标
    from PIL import Image, ImageDraw
    width, height = 64, 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.rectangle((0, 0, width, height), fill=(0, 128, 255, 255))
    dc.text((width//4, height//3), "OP", fill=(255, 255, 255, 255))
    return image

def main():
    """主函数"""
    # 创建应用实例
    app = CrossPlatformApp()
    
    # 创建托盘图标
    try:
        import pystray
        image = create_image()
        icon = pystray.Icon("Ollama Proxy", image, menu=pystray.Menu(
            pystray.MenuItem("启动中...", lambda icon, item: None, enabled=False)
        ))
        
        app.icon = icon
        app.update_menu()
        
        icon.run()
        
    except Exception:
        # 如果无法创建托盘图标，直接运行服务器
        if HAS_LOCAL_SERVER:
            app.run_server()

if __name__ == "__main__":
    main()