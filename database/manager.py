#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced database manager for Ostad Hatami Bot
"""

import json
import asyncio
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from collections import defaultdict
import gzip
import pickle

from config import config
from .models import UserData, CourseData, RegistrationData, UserStatus
from utils.cache import cache_manager
from utils.error_handler import error_handler
from utils.performance_monitor import monitor

logger = logging.getLogger(__name__)


class DataManager:
    """Enhanced user data storage management with caching, backup, and optimization"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self.data_dir = Path(config.database.path)
        self.users_dir = self.data_dir / "users"
        self.courses_dir = self.data_dir / "courses"
        self.registrations_dir = self.data_dir / "registrations"
        self.backup_dir = self.data_dir / "backups"

        # Create directories
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.courses_dir.mkdir(parents=True, exist_ok=True)
        self.registrations_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # File locks for concurrent access
        self._file_locks = defaultdict(asyncio.Lock)

        # Statistics
        self.stats = {
            "total_users": 0,
            "total_courses": 0,
            "total_registrations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "backup_count": 0,
            "last_backup": None,
        }

        # Initialize cache
        self.cache = cache_manager.get_cache("users")
        self.course_cache = cache_manager.get_cache("courses")
        self.registration_cache = cache_manager.get_cache("registrations")

        # Load initial statistics
        self._load_statistics()

        self._initialized = True

        logger.info(f"DataManager initialized with data directory: {self.data_dir}")

    def _load_statistics(self):
        """Load initial statistics from disk"""
        try:
            # Count users
            self.stats["total_users"] = len(list(self.users_dir.glob("user_*.json")))

            # Count courses
            self.stats["total_courses"] = len(
                list(self.courses_dir.glob("course_*.json"))
            )

            # Count registrations
            self.stats["total_registrations"] = len(
                list(self.registrations_dir.glob("registration_*.json"))
            )

            # Find last backup
            backup_files = list(self.backup_dir.glob("backup_*.json.gz"))
            if backup_files:
                latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
                self.stats["last_backup"] = datetime.fromtimestamp(
                    latest_backup.stat().st_mtime
                )
                self.stats["backup_count"] = len(backup_files)

        except Exception as e:
            logger.error(f"Error loading statistics: {e}")

    def get_user_file_path(self, user_id: int) -> Path:
        """Get path to user's JSON file"""
        return self.users_dir / f"user_{user_id}.json"

    def get_course_file_path(self, course_id: str) -> Path:
        """Get path to course's JSON file"""
        return self.courses_dir / f"course_{course_id}.json"

    def get_registration_file_path(self, registration_id: str) -> Path:
        """Get path to registration's JSON file"""
        return self.registrations_dir / f"registration_{registration_id}.json"

    async def save_user_data(self, user_data: UserData) -> bool:
        """Save user data with enhanced error handling and caching"""
        try:
            async with self._file_locks[user_data.user_id]:
                file_path = self.get_user_file_path(user_data.user_id)

                # Update timestamps
                user_data.last_updated = datetime.now()

                # Convert to dictionary
                data_dict = user_data.to_dict()

                # Use asyncio for file operations
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, self._write_json_file, file_path, data_dict
                )

                # Update cache
                cache_key = f"user_{user_data.user_id}"
                await self.cache.set(cache_key, data_dict)

                # Update statistics
                if not file_path.exists():
                    self.stats["total_users"] += 1

                logger.info(f"User data saved for user_id: {user_data.user_id}")
                return True

        except Exception as e:
            await error_handler.handle_error(e, "save_user_data", user_data.user_id)
            return False

    async def load_user_data(self, user_id: int) -> Optional[UserData]:
        """Load user data with caching and error handling"""
        try:
            # Check cache first
            cache_key = f"user_{user_id}"
            cached_data = await self.cache.get(cache_key)

            if cached_data:
                self.stats["cache_hits"] += 1
                return UserData.from_dict(cached_data)

            self.stats["cache_misses"] += 1

            async with self._file_locks[user_id]:
                file_path = self.get_user_file_path(user_id)

                if not file_path.exists():
                    return None

                # Use asyncio for file operations
                loop = asyncio.get_event_loop()
                data_dict = await loop.run_in_executor(
                    None, self._read_json_file, file_path
                )

                if data_dict:
                    # Cache the result
                    await self.cache.set(cache_key, data_dict)
                    return UserData.from_dict(data_dict)

                return None

        except Exception as e:
            await error_handler.handle_error(e, "load_user_data", user_id)
            return None

    async def user_exists(self, user_id: int) -> bool:
        """Check if user exists with caching"""
        # Check cache first
        cache_key = f"user_{user_id}"
        cached_data = await self.cache.get(cache_key)
        if cached_data is not None:
            return True

        # Check file system
        file_path = self.get_user_file_path(user_id)
        exists = await asyncio.get_event_loop().run_in_executor(None, file_path.exists)
        return exists

    async def delete_user_data(self, user_id: int) -> bool:
        """Delete user data"""
        try:
            async with self._file_locks[user_id]:
                file_path = self.get_user_file_path(user_id)

                if file_path.exists():
                    # Remove from cache
                    cache_key = f"user_{user_id}"
                    await self.cache.delete(cache_key)

                    # Delete file
                    await asyncio.get_event_loop().run_in_executor(
                        None, file_path.unlink
                    )

                    # Update statistics
                    self.stats["total_users"] = max(0, self.stats["total_users"] - 1)

                    logger.info(f"User data deleted for user_id: {user_id}")
                    return True

                return False

        except Exception as e:
            await error_handler.handle_error(e, "delete_user_data", user_id)
            return False

    async def get_all_users(self) -> List[UserData]:
        """Get all users with pagination support"""
        try:
            users = []
            user_files = list(self.users_dir.glob("user_*.json"))

            for file_path in user_files:
                try:
                    # Extract user ID from filename
                    user_id = int(file_path.stem.split("_")[1])

                    # Load user data
                    user_data = await self.load_user_data(user_id)
                    if user_data:
                        users.append(user_data)

                except Exception as e:
                    logger.error(f"Error loading user from {file_path}: {e}")
                    continue

            return users

        except Exception as e:
            await error_handler.handle_error(e, "get_all_users")
            return []

    async def search_users(self, criteria: Dict[str, Any]) -> List[UserData]:
        """Search users by criteria"""
        try:
            all_users = await self.get_all_users()
            results = []

            for user in all_users:
                match = True

                for key, value in criteria.items():
                    if hasattr(user, key):
                        user_value = getattr(user, key)
                        if isinstance(value, str) and isinstance(user_value, str):
                            if value.lower() not in user_value.lower():
                                match = False
                                break
                        elif user_value != value:
                            match = False
                            break
                    else:
                        match = False
                        break

                if match:
                    results.append(user)

            return results

        except Exception as e:
            await error_handler.handle_error(e, "search_users")
            return []

    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            all_users = await self.get_all_users()

            stats = {
                "total_users": len(all_users),
                "active_users": len([u for u in all_users if u.is_active()]),
                "users_by_grade": defaultdict(int),
                "users_by_major": defaultdict(int),
                "users_by_province": defaultdict(int),
                "recent_registrations": 0,
                "cache_stats": {
                    "hits": self.stats["cache_hits"],
                    "misses": self.stats["cache_misses"],
                    "hit_rate": round(
                        (
                            (
                                self.stats["cache_hits"]
                                / (
                                    self.stats["cache_hits"]
                                    + self.stats["cache_misses"]
                                )
                                * 100
                            )
                            if (self.stats["cache_hits"] + self.stats["cache_misses"])
                            > 0
                            else 0
                        ),
                        2,
                    ),
                },
            }

            # Calculate statistics
            for user in all_users:
                stats["users_by_grade"][user.grade] += 1
                stats["users_by_major"][user.major] += 1
                stats["users_by_province"][user.province] += 1

                # Count recent registrations (last 7 days)
                if user.registration_date:
                    days_ago = (datetime.now() - user.registration_date).days
                    if days_ago <= 7:
                        stats["recent_registrations"] += 1

            return stats

        except Exception as e:
            await error_handler.handle_error(e, "get_user_statistics")
            return {}

    async def create_backup(self) -> bool:
        """Create a backup of all data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.json.gz"

            # Collect all data
            backup_data = {
                "timestamp": timestamp,
                "users": [],
                "courses": [],
                "registrations": [],
                "statistics": self.stats,
            }

            # Backup users
            all_users = await self.get_all_users()
            for user in all_users:
                backup_data["users"].append(user.to_dict())

            # Backup courses (if any)
            course_files = list(self.courses_dir.glob("course_*.json"))
            for file_path in course_files:
                try:
                    data = self._read_json_file(file_path)
                    if data:
                        backup_data["courses"].append(data)
                except Exception as e:
                    logger.error(f"Error reading course file {file_path}: {e}")

            # Backup registrations (if any)
            registration_files = list(
                self.registrations_dir.glob("registration_*.json")
            )
            for file_path in registration_files:
                try:
                    data = self._read_json_file(file_path)
                    if data:
                        backup_data["registrations"].append(data)
                except Exception as e:
                    logger.error(f"Error reading registration file {file_path}: {e}")

            # Compress and save backup
            await asyncio.get_event_loop().run_in_executor(
                None, self._write_compressed_json, backup_file, backup_data
            )

            # Update statistics
            self.stats["backup_count"] += 1
            self.stats["last_backup"] = datetime.now()

            # Clean old backups
            await self._cleanup_old_backups()

            logger.info(f"Backup created: {backup_file}")
            return True

        except Exception as e:
            await error_handler.handle_error(e, "create_backup")
            return False

    async def restore_backup(self, backup_file: Path) -> bool:
        """Restore data from backup"""
        try:
            # Read backup data
            backup_data = await asyncio.get_event_loop().run_in_executor(
                None, self._read_compressed_json, backup_file
            )

            if not backup_data:
                logger.error("Invalid backup file")
                return False

            # Restore users
            for user_dict in backup_data.get("users", []):
                try:
                    user_data = UserData.from_dict(user_dict)
                    await self.save_user_data(user_data)
                except Exception as e:
                    logger.error(
                        f"Error restoring user {user_dict.get('user_id')}: {e}"
                    )

            # Restore courses
            for course_dict in backup_data.get("courses", []):
                try:
                    course_data = CourseData.from_dict(course_dict)
                    await self.save_course_data(course_data)
                except Exception as e:
                    logger.error(
                        f"Error restoring course {course_dict.get('course_id')}: {e}"
                    )

            # Restore registrations
            for reg_dict in backup_data.get("registrations", []):
                try:
                    reg_data = RegistrationData.from_dict(reg_dict)
                    await self.save_registration_data(reg_data)
                except Exception as e:
                    logger.error(
                        f"Error restoring registration {reg_dict.get('registration_id')}: {e}"
                    )

            logger.info(f"Backup restored from: {backup_file}")
            return True

        except Exception as e:
            await error_handler.handle_error(e, "restore_backup")
            return False

    async def _cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            backup_files = list(self.backup_dir.glob("backup_*.json.gz"))

            # Keep only the last N backups
            max_backups = config.database.max_backup_files
            if len(backup_files) > max_backups:
                # Sort by modification time and remove oldest
                backup_files.sort(key=lambda f: f.stat().st_mtime)
                files_to_remove = backup_files[:-max_backups]

                for file_path in files_to_remove:
                    await asyncio.get_event_loop().run_in_executor(
                        None, file_path.unlink
                    )
                    logger.info(f"Removed old backup: {file_path}")

        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")

    def _write_json_file(self, file_path: Path, data: Dict[str, Any]):
        """Write JSON file with error handling"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error writing JSON file {file_path}: {e}")
            raise

    def _read_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read JSON file with error handling"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            return None

    def _write_compressed_json(self, file_path: Path, data: Dict[str, Any]):
        """Write compressed JSON file"""
        try:
            with gzip.open(file_path, "wt", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error writing compressed JSON file {file_path}: {e}")
            raise

    def _read_compressed_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read compressed JSON file"""
        try:
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading compressed JSON file {file_path}: {e}")
            return None

    # Course management methods (placeholder for future implementation)
    async def save_course_data(self, course_data: CourseData) -> bool:
        """Save course data"""
        # Implementation for course management
        return True

    async def save_registration_data(self, registration_data: RegistrationData) -> bool:
        """Save registration data"""
        # Implementation for registration management
        return True

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        return {
            "users": await self.get_user_statistics(),
            "cache": await self.cache.get_stats(),
            "backup": {
                "count": self.stats["backup_count"],
                "last_backup": (
                    self.stats["last_backup"].isoformat()
                    if self.stats["last_backup"]
                    else None
                ),
            },
            "storage": {
                "users_dir_size": await self._get_directory_size(self.users_dir),
                "courses_dir_size": await self._get_directory_size(self.courses_dir),
                "registrations_dir_size": await self._get_directory_size(
                    self.registrations_dir
                ),
                "backup_dir_size": await self._get_directory_size(self.backup_dir),
            },
        }

    async def _get_directory_size(self, directory: Path) -> int:
        """Get directory size in bytes"""
        try:
            total_size = 0
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception:
            return 0
