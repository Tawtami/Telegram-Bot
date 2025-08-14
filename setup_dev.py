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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    logger.info(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")

    if version < (3, 8):
        logger.error("❌ Python 3.8+ is required")
        return False
    elif version < (3, 9):
        logger.warning("⚠️ Python 3.9+ is recommended for better performance")
    else:
        logger.info("✅ Python version is compatible")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    logger.info("\n📦 Checking Dependencies:")

    required_packages = ["telegram", "dotenv", "aiohttp", "pytz"]

    missing_packages = []

    for package in required_packages:
        try:
            if package == "telegram":
                import telegram

                logger.info(f"✅ {package}: {telegram.__version__}")
            elif package == "dotenv":
                import dotenv

                logger.info(f"✅ {package}: {dotenv.__version__}")
            elif package == "aiohttp":
                import aiohttp

                logger.info(f"✅ {package}: {aiohttp.__version__}")
            elif package == "pytz":
                import pytz

                logger.info(f"✅ {package}: {pytz.__version__}")
        except ImportError:
            logger.error(f"❌ {package}: Not installed")
            missing_packages.append(package)

    return missing_packages


def check_environment():
    """Check environment variables"""
    logger.info("\n🔧 Checking Environment:")

    required_vars = ["BOT_TOKEN"]
    optional_vars = ["ENVIRONMENT", "WEBHOOK_URL", "PORT"]

    missing_required = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {'***' if 'TOKEN' in var else value}")
        else:
            logger.error(f"❌ {var}: Not set")
            missing_required.append(var)

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️ {var}: Not set (optional)")

    return missing_required


def check_data_files():
    """Check if data files exist and are valid"""
    logger.info("\n📁 Checking Data Files:")

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
        logger.error("❌ data/ directory not found")
        return required_files

    for file_name in required_files:
        file_path = data_dir / file_name
        if file_path.exists():
            size = file_path.stat().st_size
            logger.info(f"✅ {file_name}: {size} bytes")
        else:
            logger.error(f"❌ {file_name}: Not found")
            missing_files.append(file_name)

    return missing_files


def check_file_permissions():
    """Check file permissions"""
    logger.info("\n🔐 Checking File Permissions:")

    files_to_check = ["bot.py", "config.py", "start.py"]

    for file_name in files_to_check:
        file_path = Path(file_name)
        if file_path.exists():
            try:
                # Try to read with UTF-8 encoding first
                with open(file_path, "r", encoding="utf-8") as f:
                    f.read(1)
                logger.info(f"✅ {file_name}: Readable (UTF-8)")
            except UnicodeDecodeError:
                try:
                    # Fallback to default encoding
                    with open(file_path, "r", encoding="cp1252") as f:
                        f.read(1)
                    logger.info(f"✅ {file_name}: Readable (CP1252)")
                except Exception as e:
                    logger.error(f"❌ {file_name}: Encoding issue - {e}")
            except PermissionError:
                logger.error(f"❌ {file_name}: Permission denied")
            except Exception as e:
                logger.error(f"❌ {file_name}: Error - {e}")
        else:
            logger.error(f"❌ {file_name}: Not found")


def provide_setup_instructions(missing_packages, missing_env_vars, missing_files):
    """Provide setup instructions"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀 SETUP INSTRUCTIONS")
    logger.info("=" * 60)

    if missing_packages:
        logger.info("\n📦 Install Missing Packages:")
        logger.info("pip install -r requirements.txt")
        logger.info("Or install individually:")
        for package in missing_packages:
            if package == "telegram":
                logger.info("pip install python-telegram-bot[webhooks]>=20.3,<21.0")
            elif package == "dotenv":
                logger.info("pip install python-dotenv>=1.0.0")
            else:
                logger.info(f"pip install {package}")

    if missing_env_vars:
        logger.info("\n🔧 Set Environment Variables:")
        logger.info("Create a .env file with:")
        for var in missing_env_vars:
            if var == "BOT_TOKEN":
                logger.info(f"{var}=your_bot_token_here")
            else:
                logger.info(f"{var}=value")

    if missing_files:
        logger.info("\n📁 Create Missing Data Files:")
        logger.info("The bot will create these automatically on first run")

    logger.info("\n💡 Quick Start:")
    logger.info("1. Set BOT_TOKEN environment variable")
    logger.info("2. Install dependencies: pip install -r requirements.txt")
    logger.info("3. Run: python start.py")

    logger.info("\n🔍 For more details, see README.md and SETUP.md")


def main():
    """Main setup check"""
    logger.info("🔍 Ostad Hatami Bot - Development Setup Check")
    logger.info("=" * 50)

    # Run all checks
    python_ok = check_python_version()
    missing_packages = check_dependencies()
    missing_env_vars = check_environment()
    missing_files = check_data_files()
    check_file_permissions()

    # Provide instructions
    provide_setup_instructions(missing_packages, missing_env_vars, missing_files)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 SUMMARY")
    logger.info("=" * 60)

    if not python_ok:
        logger.error("❌ Setup cannot proceed - Python version incompatible")
        return False

    if missing_packages:
        logger.warning(f"⚠️ {len(missing_packages)} packages need to be installed")
    else:
        logger.info("✅ All required packages are installed")

    if missing_env_vars:
        logger.warning(f"⚠️ {len(missing_env_vars)} environment variables need to be set")
    else:
        logger.info("✅ All required environment variables are set")

    if missing_files:
        logger.warning(f"⚠️ {len(missing_files)} data files are missing")
    else:
        logger.info("✅ All data files are present")

    if not missing_packages and not missing_env_vars:
        logger.info("\n🎉 Bot is ready to run!")
        return True
    else:
        logger.warning("\n⚠️ Please complete the setup before running the bot")
        return False


if __name__ == "__main__":
    main()
