#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for optimized Ostad Hatami Bot
"""

import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import modules to test
from config import config
from database import DataManager
from database.models import UserData, UserStatus, CourseData, CourseType
from utils import Validator, cache_manager, rate_limiter, monitor, error_handler


class TestOptimizedBot:
    """Test suite for optimized bot functionality"""

    def __init__(self):
        self.test_results = []
        self.temp_dir = None

    async def setup(self):
        """Setup test environment"""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

        # Override config for testing
        config.database.path = self.temp_dir
        config.performance.cache_ttl_seconds = 60
        config.performance.max_requests_per_minute = 100

        print("🧪 Test environment setup complete")

    async def teardown(self):
        """Cleanup test environment"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        print("🧹 Test environment cleaned up")

    async def test_configuration(self):
        """Test configuration management"""
        print("\n📋 Testing Configuration...")

        # Test config validation
        assert config.bot_token is not None, "Bot token should be set"
        assert config.performance.cache_ttl_seconds > 0, "Cache TTL should be positive"
        assert config.security.min_name_length > 0, "Min name length should be positive"

        # Test config to_dict
        config_dict = config.to_dict()
        assert "database" in config_dict, "Config should have database section"
        assert "performance" in config_dict, "Config should have performance section"
        assert "security" in config_dict, "Config should have security section"

        print("✅ Configuration tests passed")
        self.test_results.append("Configuration: PASS")

    async def test_validators(self):
        """Test validation utilities"""
        print("\n🔍 Testing Validators...")

        # Test name validation
        is_valid, result = Validator.validate_name("علی", "نام")
        assert is_valid, "Valid Persian name should pass"
        assert result == "علی", "Should return sanitized name"

        is_valid, result = Validator.validate_name("", "نام")
        assert not is_valid, "Empty name should fail"

        # Test phone validation
        is_valid, result = Validator.validate_phone("09121234567")
        assert is_valid, "Valid Iranian phone should pass"
        assert result.startswith("+98"), "Should normalize to international format"

        is_valid, result = Validator.validate_phone("123")
        assert not is_valid, "Invalid phone should fail"

        # Test input sanitization
        sanitized = Validator.sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in sanitized, "Should remove XSS patterns"

        print("✅ Validator tests passed")
        self.test_results.append("Validators: PASS")

    async def test_caching(self):
        """Test caching system"""
        print("\n💾 Testing Caching...")

        cache = cache_manager.get_cache("test")

        # Test basic operations
        await cache.set("test_key", "test_value")
        value = await cache.get("test_key")
        assert value == "test_value", "Should retrieve stored value"

        # Test cache statistics
        stats = await cache.get_stats()
        assert stats["hits"] >= 0, "Should have hit count"
        assert stats["misses"] >= 0, "Should have miss count"

        # Test cache expiration
        await cache.set("expire_key", "expire_value", ttl=1)
        await asyncio.sleep(2)
        value = await cache.get("expire_key")
        assert value is None, "Expired key should return None"

        print("✅ Caching tests passed")
        self.test_results.append("Caching: PASS")

    async def test_rate_limiting(self):
        """Test rate limiting"""
        print("\n⏱️ Testing Rate Limiting...")

        user_id = "test_user_123"

        # Test basic rate limiting
        for i in range(5):
            is_allowed = await rate_limiter.is_allowed(user_id)
            assert is_allowed, f"Request {i+1} should be allowed"

        # Test rate limit exceeded
        is_allowed = await rate_limiter.is_allowed(user_id)
        assert not is_allowed, "Should be rate limited after exceeding limit"

        # Test statistics
        stats = await rate_limiter.get_global_stats()
        assert stats["total_requests"] > 0, "Should have request count"
        assert stats["blocked_requests"] > 0, "Should have blocked requests"

        print("✅ Rate limiting tests passed")
        self.test_results.append("Rate Limiting: PASS")

    async def test_data_models(self):
        """Test data models"""
        print("\n📊 Testing Data Models...")

        # Test UserData model
        user_data = UserData(
            user_id=123456789,
            first_name="علی",
            last_name="رضایی",
            grade="یازدهم",
            major="ریاضی",
            province="خراسان رضوی",
            city="مشهد",
            phone="+989121234567",
        )

        assert user_data.get_full_name() == "علی رضایی", "Should return full name"
        assert user_data.is_active(), "New user should be active"

        # Test serialization
        user_dict = user_data.to_dict()
        assert "user_id" in user_dict, "Should have user_id in dict"
        assert "first_name" in user_dict, "Should have first_name in dict"

        # Test deserialization
        restored_user = UserData.from_dict(user_dict)
        assert restored_user.user_id == user_data.user_id, "Should restore user_id"
        assert (
            restored_user.first_name == user_data.first_name
        ), "Should restore first_name"

        print("✅ Data model tests passed")
        self.test_results.append("Data Models: PASS")

    async def test_database_manager(self):
        """Test database manager"""
        print("\n🗄️ Testing Database Manager...")

        data_manager = DataManager()

        # Test user data operations
        user_data = UserData(
            user_id=999999999,
            first_name="تست",
            last_name="کاربر",
            grade="دهم",
            major="تجربی",
            province="تهران",
            city="تهران",
            phone="+989876543210",
        )

        # Test save
        success = await data_manager.save_user_data(user_data)
        assert success, "Should save user data successfully"

        # Test load
        loaded_user = await data_manager.load_user_data(999999999)
        assert loaded_user is not None, "Should load user data"
        assert loaded_user.first_name == "تست", "Should load correct first name"

        # Test exists
        exists = await data_manager.user_exists(999999999)
        assert exists, "Should find existing user"

        # Test statistics
        stats = await data_manager.get_user_statistics()
        assert stats["total_users"] > 0, "Should have user count"

        print("✅ Database manager tests passed")
        self.test_results.append("Database Manager: PASS")

    async def test_performance_monitoring(self):
        """Test performance monitoring"""
        print("\n📈 Testing Performance Monitoring...")

        # Test request time logging
        await monitor.log_request_time("test_handler", 0.5, 123456)

        # Test error logging
        await monitor.log_error("TestError", "test_handler", 123456)

        # Test user activity
        await monitor.log_user_activity(123456, "test_activity")

        # Test statistics
        stats = await monitor.get_stats()
        assert "system" in stats, "Should have system stats"
        assert "handlers" in stats, "Should have handler stats"

        # Test handler stats
        handler_stats = await monitor.get_handler_stats("test_handler")
        assert handler_stats is not None, "Should have handler stats"
        assert handler_stats["total_requests"] > 0, "Should have request count"

        print("✅ Performance monitoring tests passed")
        self.test_results.append("Performance Monitoring: PASS")

    async def test_error_handling(self):
        """Test error handling"""
        print("\n🚨 Testing Error Handling...")

        # Test error handling
        error_info = await error_handler.handle_error(
            ValueError("Test error"), "test_handler", 123456, {"test": "context"}
        )

        assert error_info.error_id.startswith("ERR_"), "Should have error ID"
        assert error_info.error_type == "ValueError", "Should have correct error type"

        # Test error statistics
        error_stats = await error_handler.get_error_stats()
        assert error_stats["total_errors"] > 0, "Should have error count"

        # Test error resolution
        await error_handler.resolve_error(error_info.error_id, "Test resolution")

        # Test error details
        resolved_error = await error_handler.get_error_details(error_info.error_id)
        assert resolved_error.resolved, "Error should be marked as resolved"

        print("✅ Error handling tests passed")
        self.test_results.append("Error Handling: PASS")

    async def test_security_utils(self):
        """Test security utilities"""
        print("\n🔒 Testing Security Utils...")

        # Test input sanitization
        sanitized = SecurityUtils.sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in sanitized, "Should remove XSS patterns"

        # Test filename validation
        assert SecurityUtils.validate_filename("test.txt"), "Valid filename should pass"
        assert not SecurityUtils.validate_filename(
            "../../../etc/passwd"
        ), "Path traversal should fail"

        # Test secure token generation
        token = SecurityUtils.generate_secure_token()
        assert len(token) > 20, "Token should be sufficiently long"

        # Test HMAC
        data = "test_data"
        secret = "test_secret"
        signature = SecurityUtils.generate_hmac(data, secret)
        assert SecurityUtils.verify_hmac(
            data, signature, secret
        ), "HMAC verification should pass"

        print("✅ Security utils tests passed")
        self.test_results.append("Security Utils: PASS")

    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Optimized Bot Test Suite")
        print("=" * 50)

        try:
            await self.setup()

            # Run all tests
            await self.test_configuration()
            await self.test_validators()
            await self.test_caching()
            await self.test_rate_limiting()
            await self.test_data_models()
            await self.test_database_manager()
            await self.test_performance_monitoring()
            await self.test_error_handling()
            await self.test_security_utils()

            # Print results
            print("\n" + "=" * 50)
            print("📊 Test Results Summary:")
            print("=" * 50)

            for result in self.test_results:
                print(f"  {result}")

            print(f"\n✅ All {len(self.test_results)} tests passed!")
            print("🎉 Optimized bot is working correctly!")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            raise
        finally:
            await self.teardown()


async def main():
    """Main test function"""
    tester = TestOptimizedBot()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
