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
        except Exception as e:
            print(f"加载配置文件出错: {e}")
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
        except Exception as e:
            print(f"保存配置文件出错: {e}")
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
                    print("服务已自动启动")
                    # 更新菜单状态
                    if self.icon:
                        self.update_menu()
                    return

            # 如果多次尝试后仍未启动
            print("服务将在您手动启动时运行")
        except Exception as e:
            print(f"自动启动服务时出错: {str(e)}")

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
            print("服务已在运行中")
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
                print(f"服务已在端口 {self.port} 上运行")
                # 更新菜单状态
                if icon:
                    self.update_menu(icon)
            else:
                print("无法启动服务，请检查日志")

        except Exception as e:
            print(f"启动服务时出错: {str(e)}")

    def run_server(self):
        """在后台线程中运行服务器"""
        try:
            # 导入并运行FastAPI应用
            import uvicorn
            from main import app
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=self.port,
                log_level="info",
                access_log=False
            )
            self.server_instance = uvicorn.Server(config)
            self.server_instance.run()
        except Exception as e:
            print(f"服务器运行错误: {e}")

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
            print("服务已停止")
            
            # 更新菜单状态
            if icon:
                self.update_menu(icon)

        except Exception as e:
            print(f"停止服务时出错: {str(e)}")

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
                            print(f"端口已设置为: {new_port}\n重启服务以应用更改。")
                        else:
                            print("保存端口配置失败。")
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
                
                new_port = simpledialog.askstring(
                    "Ollama Proxy - 端口设置",
                    f"当前端口: {current_port}\n请输入新端口 (1024-65535):\n注意：修改端口后需要重启服务才能生效。",
                    initialvalue=str(current_port)
                )
                
                root.destroy()
                
                if new_port is not None:
                    try:
                        new_port = int(new_port)
                        if 1024 <= new_port <= 65535:
                            if self.save_port_config(new_port):
                                self.port = new_port
                                print(f"端口已设置为: {new_port}\n重启服务以应用更改。")
                            else:
                                print("保存端口配置失败。")
                        else:
                            print("端口必须在1024-65535之间。")
                    except ValueError:
                        print("请输入有效的端口号。")
            except Exception as e:
                print(f"创建端口输入窗口失败: {e}")

    def update_menu(self, icon=None):
        """更新菜单状态"""
        if icon is None:
            icon = self.icon
            
        if icon:
            # 更新菜单项的启用状态
            icon.menu = self.create_menu()

    def create_menu(self):
        """创建菜单"""
        import pystray
        from pystray import MenuItem as item
        
        # 根据服务状态设置菜单项的启用状态
        start_enabled = not self.is_running
        stop_enabled = self.is_running
        
        return pystray.Menu(
            item("启动服务", self.start_server, enabled=start_enabled),
            item("停止服务", self.stop_server, enabled=stop_enabled),
            pystray.Menu.SEPARATOR,
            item("端口设置", self.set_port),
            pystray.Menu.SEPARATOR,
            item("退出", self.quit_app)
        )

    def quit_app(self, icon=None, item=None):
        """退出应用"""
        try:
            # 停止服务
            if self.is_running:
                self.stop_server()

            # 退出应用
            if icon:
                icon.stop()
        except Exception as e:
            print(f"退出应用时出错: {e}")
            if icon:
                icon.stop()

    def create_image(self):
        """创建系统托盘图标"""
        try:
            from PIL import Image, ImageDraw
            import platform
            
            # macOS菜单栏图标处理
            if platform.system() == "Darwin":
                # 优先尝试加载PNG文件
                png_16_path = None
                png_32_path = None
                
                if getattr(sys, 'frozen', False):
                    # 打包后的应用
                    application_path = os.path.dirname(sys.executable)
                    resources_path = os.path.join(
                        os.path.dirname(application_path), 'Resources')
                    png_16_path = os.path.join(resources_path, 'menuicon_16.png')
                    png_32_path = os.path.join(resources_path, 'menuicon_32.png')
                else:
                    # 开发环境
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    resources_dir = os.path.join(script_dir, 'resources')
                    png_16_path = os.path.join(resources_dir, 'menuicon_16.png')
                    png_32_path = os.path.join(resources_dir, 'menuicon_32.png')
                
                # 如果16x16 PNG文件存在，使用它作为基础图标
                if png_16_path and os.path.exists(png_16_path):
                    print(f"加载16x16 PNG菜单栏图标: {png_16_path}")
                    # 加载16x16图标
                    base_image = Image.open(png_16_path)
                    
                    # 如果32x32 PNG文件也存在，将其作为高分辨率版本
                    if png_32_path and os.path.exists(png_32_path):
                        print(f"加载32x32 PNG菜单栏图标: {png_32_path}")
                        high_res_image = Image.open(png_32_path)
                        
                        # 创建一个支持多分辨率的图标
                        # 在macOS上，我们可以创建一个包含多个尺寸的图像
                        # 但pystray目前不直接支持多分辨率图标
                        # 所以我们使用16x16作为主图标，它在Retina屏幕上会自动缩放
                        return base_image
                    else:
                        # 只有16x16图标可用
                        return base_image
                
            # 如果不是macOS或PNG/SVG都不存在，使用原有逻辑
            return self.load_default_icon()
            
        except Exception as e:
            print(f"创建图标失败: {e}")
            return None

    def load_default_icon(self):
        """加载默认图标文件"""
        try:
            # 检查是否是打包后的应用
            if getattr(sys, 'frozen', False):
                # 打包后的应用
                if platform.system() == "Darwin":  # macOS
                    # 在macOS app bundle中，资源在Contents/Resources目录
                    application_path = os.path.dirname(sys.executable)
                    resources_path = os.path.join(
                        os.path.dirname(application_path), 'Resources')
                    tray_icon_path = os.path.join(resources_path, 'menuicon_32.png')
                else:  # Windows
                    tray_icon_path = os.path.join(os.getcwd(), 'wintray.ico')
                
                # 检查托盘图标文件是否存在
                if os.path.exists(tray_icon_path):
                    print(f"加载打包应用中的托盘图标: {tray_icon_path}")
                    # 使用PIL加载图标文件
                    from PIL import Image
                    return Image.open(tray_icon_path)
                else:
                    print(f"托盘图标文件不存在: {tray_icon_path}")
            else:
                # 开发环境
                if platform.system() == "Darwin":  # macOS
                    tray_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'menuicon_32.png')
                else:  # Windows
                    tray_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'wintray.ico')
                
                # 检查托盘图标文件是否存在
                if os.path.exists(tray_icon_path):
                    print(f"加载开发环境中的托盘图标: {tray_icon_path}")
                    # 使用PIL加载图标文件
                    from PIL import Image
                    return Image.open(tray_icon_path)
                else:
                    print(f"托盘图标文件不存在: {tray_icon_path}")
        except Exception as e:
            print(f"加载托盘图标失败: {e}")
        
        return None

    def run(self):
        """运行系统托盘应用"""
        # 设置工作目录为脚本所在目录
        try:
            # 如果是打包后的应用，使用资源目录
            if getattr(sys, 'frozen', False):
                # 运行在打包后的环境
                application_path = os.path.dirname(sys.executable)
                if platform.system() == "Darwin":  # macOS
                    # 在macOS app bundle中，资源在Contents/Resources目录
                    if sys.platform == 'darwin':
                        resources_path = os.path.join(
                            os.path.dirname(application_path), 'Resources')
                        if os.path.exists(resources_path):
                            os.chdir(resources_path)
                        else:
                            os.chdir(application_path)
                    else:
                        os.chdir(application_path)
                else:  # Windows
                    os.chdir(application_path)
            else:
                # 运行在开发环境
                os.chdir(os.path.dirname(os.path.abspath(__file__)))
        except Exception as e:
            print(f"设置工作目录失败: {e}")

        # 创建菜单
        try:
            import pystray
            from pystray import MenuItem as item
            
            # 创建图标
            image = self.create_image()
            if image is None:
                print("警告: 无法加载托盘图标文件，使用默认图标")
                # 如果无法创建图像，使用默认图像
                from PIL import Image, ImageDraw
                image = Image.new('RGB', (64, 64), (255, 255, 255))
                dc = ImageDraw.Draw(image)
                # 使用更明显的默认图标
                dc.text((10, 10), "🦙", fill=(0, 0, 0))
                dc.rectangle((5, 5, 59, 59), outline=(0, 0, 0), width=2)
            else:
                print("成功加载托盘图标文件")
            
            # 创建系统托盘图标
            self.icon = pystray.Icon("Ollama Proxy", image, "Ollama Proxy", self.create_menu())
            self.icon.run()
        except ImportError:
            print("缺少必要的依赖库，请安装 pystray")
            sys.exit(1)

if __name__ == "__main__":
    # 启动应用
    try:
        app = CrossPlatformApp()
        app.run()
    except Exception as e:
        print(f"应用启动失败: {e}")
        import traceback
        traceback.print_exc()