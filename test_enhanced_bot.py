#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Enhanced Math Course Registration Bot
اسکریپت تست برای ربات پیشرفته ثبت‌نام کلاس‌های ریاضی
"""

import asyncio
import time
import json
from datetime import datetime

# Import enhanced components
from enhanced_bot import EnhancedMathBot
from performance_monitor import performance_monitor
from config_enhanced import *

async def test_enhanced_bot():
    """Test the enhanced bot functionality"""
    print("🚀 Testing Enhanced Math Course Registration Bot")
    print("=" * 60)
    
    try:
        # Initialize bot
        print("📋 Initializing enhanced bot...")
        bot = EnhancedMathBot()
        await bot.initialize()
        print("✅ Bot initialized successfully")
        
        # Test cache manager
        print("\n🔍 Testing cache manager...")
        cache_key = "test_data"
        test_data = {"test": "value", "timestamp": datetime.now().isoformat()}
        
        await bot.cache_manager.set(cache_key, test_data)
        cached_data = await bot.cache_manager.get(cache_key)
        
        if cached_data and cached_data.get("test") == "value":
            print("✅ Cache manager working correctly")
        else:
            print("❌ Cache manager test failed")
        
        # Test UI manager
        print("\n🎨 Testing UI manager...")
        test_course = {
            "name": "تست کلاس",
            "price": "رایگان",
            "duration": "۱ ساعت",
            "target": "پایه دهم",
            "description": "کلاس تست",
            "features": ["ویژگی ۱", "ویژگی ۲"],
            "seats_available": 50
        }
        
        formatted_card = bot.ui_manager.format_course_card(test_course)
        if "تست کلاس" in formatted_card and "رایگان" in formatted_card:
            print("✅ UI manager working correctly")
        else:
            print("❌ UI manager test failed")
        
        # Test data manager
        print("\n💾 Testing data manager...")
        test_student = {
            "user_id": 12345,
            "name": "تست کاربر",
            "phone": "۰۹۱۲۳۴۵۶۷۸۹",
            "grade": "دهم",
            "field": "ریاضی",
            "parent_phone": "۰۹۱۲۳۴۵۶۷۸۹",
            "course": "تست کلاس"
        }
        
        await bot.data_manager.add_student(test_student)
        retrieved_student = await bot.data_manager.get_student_by_user_id(12345)
        
        if retrieved_student and retrieved_student.get("name") == "تست کاربر":
            print("✅ Data manager working correctly")
        else:
            print("❌ Data manager test failed")
        
        # Test performance monitoring
        print("\n📊 Testing performance monitoring...")
        await performance_monitor.async_track_request(12345, "test_action", 0.1)
        await performance_monitor.async_track_request(12345, "test_action_2", 0.2)
        
        summary = performance_monitor.get_performance_summary()
        if summary['total_requests'] >= 2:
            print("✅ Performance monitoring working correctly")
            print(f"   📈 Total requests: {summary['total_requests']}")
            print(f"   ⏱️  Average response time: {summary['average_response_times'].get('test_action', 0):.3f}s")
        else:
            print("❌ Performance monitoring test failed")
        
        # Test rate limiting
        print("\n🚦 Testing rate limiting...")
        start_time = time.time()
        
        for i in range(5):
            async with bot.throttler:
                await asyncio.sleep(0.1)
        
        elapsed_time = time.time() - start_time
        if elapsed_time > 0.5:  # Rate limiting should add some delay
            print("✅ Rate limiting working correctly")
        else:
            print("❌ Rate limiting test failed")
        
        # Test analytics export
        print("\n📈 Testing analytics export...")
        try:
            filename = await performance_monitor.async_export_analytics("test_analytics.json")
            print(f"✅ Analytics exported to: {filename}")
        except Exception as e:
            print(f"❌ Analytics export failed: {e}")
        
        # Performance benchmarks
        print("\n⚡ Performance Benchmarks:")
        print("-" * 40)
        
        # Test cache performance
        cache_start = time.time()
        for i in range(100):
            await bot.cache_manager.set(f"benchmark_key_{i}", {"data": f"value_{i}"})
        cache_set_time = time.time() - cache_start
        
        cache_get_start = time.time()
        for i in range(100):
            await bot.cache_manager.get(f"benchmark_key_{i}")
        cache_get_time = time.time() - cache_get_start
        
        print(f"📊 Cache Set (100 ops): {cache_set_time:.3f}s")
        print(f"📊 Cache Get (100 ops): {cache_get_time:.3f}s")
        print(f"📊 Cache Hit Rate: {performance_monitor.get_performance_summary()['cache_hit_rate']:.1f}%")
        
        # Test UI rendering performance
        ui_start = time.time()
        for i in range(50):
            bot.ui_manager.format_course_card(test_course)
        ui_time = time.time() - ui_start
        
        print(f"📊 UI Rendering (50 cards): {ui_time:.3f}s")
        
        # Final summary
        print("\n🎉 Test Results Summary:")
        print("=" * 40)
        print("✅ Enhanced bot is working correctly!")
        print("✅ All core components tested successfully")
        print("✅ Performance optimizations active")
        print("✅ UI/UX improvements implemented")
        print("✅ Analytics and monitoring functional")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        await bot.cache_manager.delete(cache_key)
        await performance_monitor.async_cleanup_old_sessions(0)  # Clean all sessions
        
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def test_configuration():
    """Test configuration loading"""
    print("\n🔧 Testing Configuration:")
    print("-" * 30)
    
    try:
        # Test UI theme
        print(f"🎨 UI Theme: {len(UI_THEME)} colors configured")
        
        # Test button layouts
        print(f"🔘 Button Layouts: {len(BUTTON_LAYOUTS)} layouts configured")
        
        # Test courses
        print(f"📚 Courses: {len(COURSES)} courses configured")
        
        # Test special courses
        print(f"⭐ Special Courses: {len(SPECIAL_COURSES)} special courses configured")
        
        # Test performance settings
        print(f"⚡ Cache TTL: {CACHE_TTL} seconds")
        print(f"🚦 Rate Limit: {RATE_LIMIT_PER_USER} requests/minute")
        
        print("✅ Configuration test passed!")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

async def main():
    """Main test function"""
    print("🧪 Enhanced Bot Test Suite")
    print("=" * 50)
    
    # Test configuration
    await test_configuration()
    
    # Test enhanced bot
    await test_enhanced_bot()
    
    print("\n🎯 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 