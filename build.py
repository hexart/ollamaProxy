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

        # First, generate the spec file
        spec_cmd = [
            "pyi-makespec",
            "--name=OllamaProxy",
            "--windowed",
            "--hidden-import=pystray",
            "--hidden-import=PIL",
            "app.py"
        ]
        # Adjust spec generation parameters based on platform
        if platform.system() == "Darwin":  # macOS
            spec_cmd.extend([
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

            spec_cmd.extend(["--target-architecture", target_arch])
            print(
                f"Target architecture for macOS: {target_arch} (detected: {current_arch})")
        else:  # Windows
            spec_cmd.extend([
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

        # Generate spec file
        subprocess.run(spec_cmd, check=True)
        print("Spec file generated successfully")

        # Modify spec file for platform-specific settings
        if platform.system() == "Darwin" and os.path.exists(spec_file):
            print("Modifying spec file to add LSUIElement for hiding dock icon...")
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec_content = f.read()

            # 在app参数中添加info_plist设置
            # 查找app = BUNDLE(...)的位置
            if "app = BUNDLE(" in spec_content:
                # 在BUNDLE参数中添加info_plist设置
                bundle_pattern = r"(app = BUNDLE\([^)]+)\)"
                import re
                match = re.search(bundle_pattern, spec_content, re.DOTALL)
                if match:
                    bundle_content = match.group(1)
                    if "info_plist=" not in bundle_content:
                        # 检查最后一个字符是否是逗号，如果不是就添加逗号
                        bundle_content = bundle_content.rstrip()
                        if bundle_content.endswith(','):
                            new_bundle = bundle_content + \
                                "\n    info_plist={'LSUIElement': True}"
                        else:
                            new_bundle = bundle_content + \
                                ",\n    info_plist={'LSUIElement': True}"

                        spec_content = spec_content.replace(
                            match.group(0), new_bundle + ")")

                        with open(spec_file, 'w', encoding='utf-8') as f:
                            f.write(spec_content)
                        print("Added LSUIElement to spec file")
                    else:
                        print("info_plist already exists in spec file")
                else:
                    print("Warning: Could not find BUNDLE section in spec file")
            else:
                print("Warning: Could not find app = BUNDLE in spec file")

        # Build using the modified spec file
        build_cmd = ["pyinstaller", "--noconfirm", spec_file]
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
            f.write(
                '{"port": 8000, "ollama_base_url": "http://localhost:11434", "timeout": 60.0}')

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
            print(
                "1. Copy the entire OllamaProxy folder to your desired installation location")
            print("2. Double-click OllamaProxy.exe to start the application")
            print("3. Make sure Ollama service is running")

        print("\nBuild completed successfully!")
    else:
        print("\nBuild failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
