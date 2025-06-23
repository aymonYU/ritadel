"""
Rate Limiter Module

简单而有效的速率限制器，防止对Yahoo Finance的请求过于频繁
"""

import time
import threading
from collections import deque


class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_requests_per_minute: int = 30):
        self.max_requests = max_requests_per_minute
        self.request_times = deque()
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """如果需要，等待以符合速率限制"""
        with self.lock:
            now = time.time()
            
            # 清理超过1分钟的旧请求记录
            while self.request_times and now - self.request_times[0] > 60:
                self.request_times.popleft()
            
            # 如果请求数达到限制，等待
            if len(self.request_times) >= self.max_requests:
                wait_time = 60 - (now - self.request_times[0]) + 1
                if wait_time > 0:
                    print(f"⏳ Rate limit reached, waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
            
            # 记录这次请求
            self.request_times.append(now)


# 全局速率限制器实例
_rate_limiter = RateLimiter()


def wait_if_needed():
    """等待以符合速率限制（便捷函数）"""
    _rate_limiter.wait_if_needed()


def configure_rate_limit(max_requests_per_minute: int):
    """配置速率限制"""
    global _rate_limiter
    _rate_limiter = RateLimiter(max_requests_per_minute)
    print(f"✅ Rate limit configured: {max_requests_per_minute} requests/minute")


def get_rate_limit_status():
    """获取当前速率限制状态"""
    with _rate_limiter.lock:
        now = time.time()
        # 清理旧记录
        while _rate_limiter.request_times and now - _rate_limiter.request_times[0] > 60:
            _rate_limiter.request_times.popleft()
        
        return {
            "max_requests_per_minute": _rate_limiter.max_requests,
            "current_requests_in_last_minute": len(_rate_limiter.request_times),
            "remaining_requests": max(0, _rate_limiter.max_requests - len(_rate_limiter.request_times))
        } 