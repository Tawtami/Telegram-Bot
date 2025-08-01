#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Monitoring and Analytics Module
ماژول نظارت بر عملکرد و تحلیل داده‌ها
"""

import time
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()

class PerformanceMonitor:
    """Performance monitoring and analytics system"""
    
    def __init__(self):
        self.metrics = {
            'requests': defaultdict(int),
            'response_times': defaultdict(list),
            'errors': defaultdict(int),
            'user_actions': defaultdict(int),
            'conversions': defaultdict(int),
            'cache_hits': 0,
            'cache_misses': 0,
            'database_operations': defaultdict(int)
        }
        
        self.user_sessions = {}
        self.conversion_funnels = defaultdict(list)
        self.performance_history = deque(maxlen=1000)
        
        # Start monitoring
        self.start_time = time.time()
        self.is_monitoring = True
    
    def track_request(self, user_id: int, action: str, response_time: float = None):
        """Track user request"""
        timestamp = datetime.now()
        
        # Track basic metrics
        self.metrics['requests'][action] += 1
        
        if response_time:
            self.metrics['response_times'][action].append(response_time)
            # Keep only last 100 response times per action
            if len(self.metrics['response_times'][action]) > 100:
                self.metrics['response_times'][action] = self.metrics['response_times'][action][-100:]
        
        # Track user session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'first_seen': timestamp,
                'last_seen': timestamp,
                'actions': [],
                'total_requests': 0
            }
        
        self.user_sessions[user_id]['last_seen'] = timestamp
        self.user_sessions[user_id]['total_requests'] += 1
        self.user_sessions[user_id]['actions'].append({
            'action': action,
            'timestamp': timestamp,
            'response_time': response_time
        })
        
        # Track conversion funnel
        if action in ['start_registration', 'confirm_registration', 'payment_completed']:
            self.conversion_funnels[user_id].append({
                'action': action,
                'timestamp': timestamp
            })
    
    def track_error(self, action: str, error_type: str, error_message: str):
        """Track errors"""
        self.metrics['errors'][f"{action}_{error_type}"] += 1
        logger.error(f"Error in {action}: {error_type} - {error_message}")
    
    def track_user_action(self, user_id: int, action: str):
        """Track user actions for analytics"""
        self.metrics['user_actions'][action] += 1
        
        # Track conversion events
        if action in ['registration_completed', 'payment_completed']:
            self.metrics['conversions'][action] += 1
    
    def track_cache_operation(self, hit: bool):
        """Track cache operations"""
        if hit:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
    
    def track_database_operation(self, operation: str, duration: float):
        """Track database operations"""
        self.metrics['database_operations'][operation] += 1
        self.metrics['response_times'][f"db_{operation}"].append(duration)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        uptime = time.time() - self.start_time
        
        # Calculate averages
        avg_response_times = {}
        for action, times in self.metrics['response_times'].items():
            if times:
                avg_response_times[action] = sum(times) / len(times)
        
        # Calculate cache hit rate
        total_cache_ops = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = (self.metrics['cache_hits'] / total_cache_ops * 100) if total_cache_ops > 0 else 0
        
        # Calculate conversion rates
        total_registrations = self.metrics['requests'].get('start_registration', 0)
        completed_registrations = self.metrics['conversions'].get('registration_completed', 0)
        conversion_rate = (completed_registrations / total_registrations * 100) if total_registrations > 0 else 0
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'total_requests': sum(self.metrics['requests'].values()),
            'requests_per_action': dict(self.metrics['requests']),
            'average_response_times': avg_response_times,
            'error_counts': dict(self.metrics['errors']),
            'cache_hit_rate': cache_hit_rate,
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'conversion_rate': conversion_rate,
            'active_users': len(self.user_sessions),
            'database_operations': dict(self.metrics['database_operations'])
        }
    
    def get_user_analytics(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get analytics for specific user"""
        if user_id not in self.user_sessions:
            return None
        
        session = self.user_sessions[user_id]
        actions = session['actions']
        
        # Calculate user metrics
        action_counts = defaultdict(int)
        for action in actions:
            action_counts[action['action']] += 1
        
        avg_response_time = 0
        if actions:
            response_times = [a['response_time'] for a in actions if a['response_time']]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'user_id': user_id,
            'first_seen': session['first_seen'],
            'last_seen': session['last_seen'],
            'total_requests': session['total_requests'],
            'action_counts': dict(action_counts),
            'average_response_time': avg_response_time,
            'conversion_funnel': self.conversion_funnels.get(user_id, [])
        }
    
    def get_conversion_funnel(self) -> Dict[str, Any]:
        """Get conversion funnel analysis"""
        funnel_stages = ['start_registration', 'enter_name', 'enter_phone', 'enter_grade', 'enter_field', 'enter_parent_phone', 'confirm_registration']
        
        funnel_data = {}
        for i, stage in enumerate(funnel_stages):
            count = self.metrics['requests'].get(stage, 0)
            funnel_data[stage] = {
                'count': count,
                'stage': i + 1
            }
        
        # Calculate drop-off rates
        for i in range(len(funnel_stages) - 1):
            current_stage = funnel_stages[i]
            next_stage = funnel_stages[i + 1]
            
            current_count = funnel_data[current_stage]['count']
            next_count = funnel_data[next_stage]['count']
            
            if current_count > 0:
                drop_off_rate = ((current_count - next_count) / current_count) * 100
                funnel_data[next_stage]['drop_off_rate'] = drop_off_rate
        
        return funnel_data
    
    def export_analytics(self, filename: str = None) -> str:
        """Export analytics data"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_{timestamp}.json"
        
        analytics_data = {
            'timestamp': datetime.now().isoformat(),
            'performance_summary': self.get_performance_summary(),
            'conversion_funnel': self.get_conversion_funnel(),
            'user_sessions_count': len(self.user_sessions),
            'top_actions': dict(sorted(self.metrics['user_actions'].items(), key=lambda x: x[1], reverse=True)[:10])
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analytics_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Analytics exported to {filename}")
        return filename
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old user sessions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_sessions = []
        
        for user_id, session in self.user_sessions.items():
            if session['last_seen'] < cutoff_time:
                old_sessions.append(user_id)
        
        for user_id in old_sessions:
            del self.user_sessions[user_id]
        
        if old_sessions:
            logger.info(f"Cleaned up {len(old_sessions)} old user sessions")
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            'requests': defaultdict(int),
            'response_times': defaultdict(list),
            'errors': defaultdict(int),
            'user_actions': defaultdict(int),
            'conversions': defaultdict(int),
            'cache_hits': 0,
            'cache_misses': 0,
            'database_operations': defaultdict(int)
        }
        self.start_time = time.time()
        logger.info("Performance metrics reset")

class AsyncPerformanceMonitor(PerformanceMonitor):
    """Async version of performance monitor"""
    
    async def async_track_request(self, user_id: int, action: str, response_time: float = None):
        """Async track user request"""
        await asyncio.get_event_loop().run_in_executor(
            None, self.track_request, user_id, action, response_time
        )
    
    async def async_export_analytics(self, filename: str = None) -> str:
        """Async export analytics data"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.export_analytics, filename
        )
    
    async def async_cleanup_old_sessions(self, max_age_hours: int = 24):
        """Async cleanup old user sessions"""
        await asyncio.get_event_loop().run_in_executor(
            None, self.cleanup_old_sessions, max_age_hours
        )

# Global performance monitor instance
performance_monitor = AsyncPerformanceMonitor()

def track_performance(func):
    """Decorator to track function performance"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        user_id = None
        
        # Try to extract user_id from args
        for arg in args:
            if hasattr(arg, 'effective_user'):
                user_id = arg.effective_user.id
                break
            elif hasattr(arg, 'from_user'):
                user_id = arg.from_user.id
                break
        
        try:
            result = await func(*args, **kwargs)
            response_time = time.time() - start_time
            
            # Track successful request
            if user_id:
                await performance_monitor.async_track_request(
                    user_id, func.__name__, response_time
                )
            
            return result
        except Exception as e:
            response_time = time.time() - start_time
            
            # Track error
            performance_monitor.track_error(func.__name__, type(e).__name__, str(e))
            
            if user_id:
                await performance_monitor.async_track_request(
                    user_id, f"{func.__name__}_error", response_time
                )
            
            raise
    
    return wrapper 