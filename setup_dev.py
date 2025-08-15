#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Development Setup Script for Ostad Hatami Bot
This script checks the environment and provides setup guidance
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Keep logger for internal/debug, but tests expect print output for user messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")

    if version < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    elif version < (3, 9):
        print("⚠️ Python 3.9+ is recommended for better performance")
    else:
        print("✅ Python version is compatible")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking Dependencies:")

    required_packages = ["telegram", "dotenv", "aiohttp", "pytz"]

    missing_packages = []

    for package in required_packages:
        try:
            if package == "telegram":
                import telegram

                print(f"✅ {package}: {telegram.__version__}")
            elif package == "dotenv":
                import dotenv

                print(f"✅ {package}: {dotenv.__version__}")
            elif package == "aiohttp":
                import aiohttp

                print(f"✅ {package}: {aiohttp.__version__}")
            elif package == "pytz":
                import pytz

                print(f"✅ {package}: {pytz.__version__}")
        except ImportError:
            print(f"❌ {package}: Not installed")
            missing_packages.append(package)

    return missing_packages


def check_environment():
    """Check environment variables"""
    print("\n🔧 Checking Environment:")

    required_vars = ["BOT_TOKEN"]
    optional_vars = ["ENVIRONMENT", "WEBHOOK_URL", "PORT"]

    missing_required = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'***' if 'TOKEN' in var else value}")
        else:
            print(f"❌ {var}: Not set")
            missing_required.append(var)

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print("⚠️ PORT: Not set (optional)" if var == "PORT" else f"⚠️ {var}: Not set (optional)")

    return missing_required


def check_data_files():
    """Check if data files exist and are valid"""
    print("\n📁 Checking Data Files:")

    data_dir = Path("data")
    required_files = [
        "students.json",
        "courses.json",
        "books.json",
        "purchases.json",
        "notifications.json",
    ]

    missing_files = []

    if not data_dir.exists():
        print("❌ data/ directory not found")
        return required_files

    for file_name in required_files:
        file_path = data_dir / file_name
        if file_path.exists():
            # Try to read content first (works with patched read_text in tests),
            # then fall back to stat size; handle missing file gracefully.
            size = 0
            try:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    size = len(content.encode("utf-8"))
                except Exception:
                    size = file_path.stat().st_size
            except Exception:
                size = 0
            print(f"✅ {file_name}: {size} bytes")
        else:
            print(f"❌ {file_name}: Not found")
            missing_files.append(file_name)

    return missing_files


def check_file_permissions():
    """Check file permissions"""
    print("\n🔐 Checking File Permissions:")

    files_to_check = ["bot.py", "config.py", "start.py"]

    for file_name in files_to_check:
        file_path = Path(file_name)
        if file_path.exists():
            try:
                # Try to read with UTF-8 encoding first
                with open(file_path, "r", encoding="utf-8") as f:
                    f.read(1)
                print(f"✅ {file_name}: Readable (UTF-8)")
            except UnicodeDecodeError:
                try:
                    # Fallback to default encoding
                    with open(file_path, "r", encoding="cp1252") as f:
                        f.read(1)
                    print(f"✅ {file_name}: Readable (CP1252)")
                except Exception as e:
                    print(f"❌ {file_name}: Encoding issue - {e}")
            except PermissionError:
                print(f"❌ {file_name}: Permission denied")
            except Exception as e:
                print(f"❌ {file_name}: Error - {e}")
        else:
            print(f"❌ {file_name}: Not found")


def provide_setup_instructions(missing_packages, missing_env_vars, missing_files):
    """Provide setup instructions"""
    print("\n" + "=" * 60)
    print("🚀 SETUP INSTRUCTIONS")
    print("=" * 60)

    if missing_packages:
        print("\n📦 Install Missing Packages:")
        print("pip install -r requirements.txt")
        print("Or install individually:")
        for package in missing_packages:
            if package == "telegram":
                print("pip install python-telegram-bot[webhooks]>=20.3,<21.0")
            elif package == "dotenv":
                print("pip install python-dotenv>=1.0.0")
            else:
                print(f"pip install {package}")

    if missing_env_vars:
        print("\n🔧 Set Environment Variables:")
        print("Create a .env file with:")
        for var in missing_env_vars:
            if var == "BOT_TOKEN":
                print(f"{var}=your_bot_token_here")
            else:
                print(f"{var}=value")

    if missing_files:
        print("\n📁 Create Missing Data Files:")
        print("The bot will create these automatically on first run")

    print("\n💡 Quick Start:")
    print("1. Set BOT_TOKEN environment variable")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run: python start.py")

    print("\n🔍 For more details, see README.md and SETUP.md")


def main():
    """Main setup check"""
    print("🔍 Ostad Hatami Bot - Development Setup Check")
    print("=" * 50)

    # Run all checks
    python_ok = check_python_version()
    missing_packages = check_dependencies()
    missing_env_vars = check_environment()
    missing_files = check_data_files()
    check_file_permissions()

    # Provide instructions
    provide_setup_instructions(missing_packages, missing_env_vars, missing_files)

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    if not python_ok:
        print("❌ Setup cannot proceed - Python version incompatible")
        return False

    if missing_packages:
        print(f"⚠️ {len(missing_packages)} packages need to be installed")
    else:
        print("✅ All required packages are installed")

    if missing_env_vars:
        print(f"⚠️ {len(missing_env_vars)} environment variables need to be set")
    else:
        print("✅ All required environment variables are set")

    if missing_files:
        print(f"⚠️ {len(missing_files)} data files are missing")
    else:
        print("✅ All data files are present")

    if not missing_packages and not missing_env_vars:
        print("\n🎉 Bot is ready to run!")
        return True
    else:
        print("\n⚠️ Please complete the setup before running the bot")
        return False


if __name__ == "__main__":
    main()
