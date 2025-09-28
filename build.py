#!/usr/bin/env python3
"""
Ollama Proxy Cross-platform Client Packaging Tool
"""

import os
import sys
import subprocess
import platform

def install_build_dependencies():
    """Install build dependencies - this should be done by the build script"""
    print("Build dependencies should already be installed by build script")
    return True

def build_app():
    """Build application"""
    print("Building application...")
    try:
        # Remove existing spec file to allow PyInstaller to generate a new one
        spec_file = "OllamaProxy.spec"
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print("Removed existing spec file to allow regeneration")
        
        # Build command using pyinstaller directly (not as module)
        build_cmd = [
            "pyinstaller",
            "--name=OllamaProxy",
            "--windowed",  # GUI application without console window
            "--noconfirm",  # Don't ask for confirmation when removing output directory
            "--hidden-import=pystray",
            "--hidden-import=PIL",
            "app.py"
        ]
        
        # Adjust parameters based on platform
        if platform.system() == "Darwin":  # macOS
            build_cmd.extend([
                "--icon=resources/mac.icns",
                "--add-data=resources:resources",
                "--add-data=main.py:.",
                "--add-data=config.py:.",
                "--add-data=config.json:.",
                "--add-data=resources/menuicon_16.png:.",
                "--add-data=resources/menuicon_32.png:.",
                "--osx-bundle-identifier", "com.ollama.proxy"
            ])
            
            # 根据当前系统架构自动选择目标架构
            current_arch = platform.machine().lower()
            if current_arch in ['arm64', 'aarch64']:
                target_arch = "arm64"
            elif current_arch in ['x86_64', 'amd64']:
                target_arch = "x86_64"
            else:
                # 如果无法识别架构，使用当前架构
                target_arch = current_arch
            
            build_cmd.extend(["--target-architecture", target_arch])
            print(f"Target architecture for macOS: {target_arch} (detected: {current_arch})")
        else:  # Windows
            build_cmd.extend([
                "--icon=resources/wintray.ico",
                "--add-data=resources;resources",
                "--add-data=main.py;.",
                "--add-data=config.py;.",
                "--add-data=config.json;.",
                "--add-data=resources/wintray.ico;."
            ])
            
            # Windows架构检测和提示
            current_arch = platform.machine().lower()
            if current_arch in ['arm64', 'aarch64']:
                print(f"Detected ARM64 Windows architecture: {current_arch}")
                print("Note: Building for ARM64 Windows")
            elif current_arch in ['x86_64', 'amd64']:
                print(f"Detected x64 Windows architecture: {current_arch}")
            else:
                print(f"Detected Windows architecture: {current_arch}")
        
        subprocess.run(build_cmd, check=True)
        print("Application build completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Application build failed: {e}")
        return False

def create_app_structure():
    """Create application directory structure"""
    # Ensure required files exist
    required_files = ['app.py', 'main.py', 'config.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"Error: Missing required file {file}")
            return False
    
    # Create config.json if it doesn't exist
    if not os.path.exists('config.json'):
        with open('config.json', 'w', encoding='utf-8') as f:
            f.write('{"port": 8000, "ollama_base_url": "http://localhost:11434", "timeout": 60.0}')
    
    return True

def create_platform_scripts():
    """Create platform-specific scripts"""
    # No service scripts needed as per user request
    print("Skipping service script creation as per user request")

def install_requirements():
    """Install requirements - this should be done by the build script"""
    print("Application dependencies should already be installed by build script")
    return True

def main():
    """Main function"""
    print("Ollama Proxy Cross-platform Client Packaging Tool")
    print("=" * 40)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    
    # Print system information
    print(f"Platform: {platform.system()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Platform details: {platform.platform()}")
    
    # Create application structure
    if not create_app_structure():
        return
    
    # Create platform-specific scripts
    create_platform_scripts()
    
    # Build application
    success = build_app()
    if success:
        if platform.system() == "Darwin":  # macOS
            print("\nmacOS application packaging completed!")
            print("Application location: dist/OllamaProxy.app")
            print("\nInstructions:")
            print("1. Drag OllamaProxy.app to the Applications folder")
            print("2. First run may require granting permissions in System Preferences")
            print("3. Make sure Ollama service is running")
        else:  # Windows or other platforms
            print("\nApplication packaging completed!")
            print("Application location: dist/OllamaProxy/")
            print("\nInstructions:")
            print("1. Copy the entire OllamaProxy folder to your desired installation location")
            print("2. Double-click OllamaProxy.exe to start the application")
            print("3. Make sure Ollama service is running")
        
        print("\nBuild completed successfully!")
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()