"""
YFinance Rate Limiter Module

这个模块提供了 YFinance API 请求的速率限制功能，防止因过于频繁的请求而被限制访问。

主要功能：
- 线程安全的速率限制
- 可配置的请求频率控制
- 实时使用情况监控
- 限流器重置功能
"""

import time
import threading
from typing import Dict, Any


class YFinanceRateLimit:
    """YFinance API 速率限制器
    
    这个类提供线程安全的速率限制功能，确保在指定时间窗口内
    不会超过最大请求数量。
    """
    
    def __init__(self, max_requests_per_minute: int = 30):
        """初始化速率限制器
        
        Args:
            max_requests_per_minute: 每分钟最大请求数，默认30个
        """
        self.max_requests = max_requests_per_minute
        self.requests = []  # 存储请求时间戳
        self.lock = threading.Lock()  # 线程锁
    
    def wait_if_needed(self) -> None:
        """如果需要，等待直到可以发出下一个请求"""
        with self.lock:
            now = time.time()
            # 优化：只保留最近1分钟的请求记录，避免列表过长
            cutoff_time = now - 60
            self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            if len(self.requests) >= self.max_requests:
                # 计算需要等待的时间：最老请求 + 60秒 - 当前时间
                wait_time = self.requests[0] + 60 - now + 0.1  # 添加小缓冲
                if wait_time > 0:
                    print(f"Rate limit reached, waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    # 等待后重新清理过期请求
                    now = time.time()
                    cutoff_time = now - 60
                    self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            # 记录当前请求时间
            self.requests.append(now)
    
    def get_current_usage(self) -> int:
        """获取当前1分钟内的请求数量（用于调试和监控）
        
        Returns:
            当前1分钟内的请求数量
        """
        with self.lock:
            now = time.time()
            cutoff_time = now - 60
            recent_requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            return len(recent_requests)
    
    def get_available_requests(self) -> int:
        """获取当前可用的请求数量
        
        Returns:
            当前可用的请求数量
        """
        return max(0, self.max_requests - self.get_current_usage())
    
    def reset(self) -> None:
        """重置限流器（清除所有请求记录）
        
        用于测试或紧急重置情况
        """
        with self.lock:
            self.requests.clear()
            print("Rate limiter has been reset")
    
    def get_status(self) -> Dict[str, Any]:
        """获取限流器当前状态
        
        Returns:
            包含限流器状态信息的字典
        """
        return {
            "max_requests_per_minute": self.max_requests,
            "current_usage": self.get_current_usage(),
            "available_requests": self.get_available_requests(),
            "next_reset_in_seconds": self._get_next_reset_time()
        }
    
    def _get_next_reset_time(self) -> float:
        """获取下次重置时间（最老请求过期的时间）
        
        Returns:
            距离下次重置的秒数
        """
        with self.lock:
            if not self.requests:
                return 0.0
            
            now = time.time()
            oldest_request = min(self.requests)
            reset_time = oldest_request + 60 - now
            return max(0.0, reset_time)


# 全局限流器实例
_rate_limiter = YFinanceRateLimit()


def configure_yfinance_rate_limit(max_requests_per_minute: int = 30) -> None:
    """配置 YFinance 请求的速率限制
    
    Args:
        max_requests_per_minute: 每分钟最大请求数（默认: 30）
    """
    global _rate_limiter
    _rate_limiter = YFinanceRateLimit(max_requests_per_minute)
    print(f"✅ YFinance rate limit configured: {max_requests_per_minute} requests per minute")


def get_rate_limit_status() -> Dict[str, Any]:
    """获取当前限流状态信息
    
    Returns:
        包含限流状态的字典：
        - max_requests_per_minute: 每分钟最大请求数
        - current_usage: 当前1分钟内已使用的请求数
        - available_requests: 当前可用的请求数
        - next_reset_in_seconds: 距离下次重置的秒数
    """
    return _rate_limiter.get_status()


def wait_if_needed() -> None:
    """等待直到可以发出下一个请求（如果需要的话）"""
    _rate_limiter.wait_if_needed()


def reset_rate_limiter() -> None:
    """重置速率限制器"""
    _rate_limiter.reset()


def get_rate_limiter() -> YFinanceRateLimit:
    """获取全局速率限制器实例
    
    Returns:
        全局速率限制器实例
    """
    return _rate_limiter


# 使用示例和测试函数
def demo_rate_limiter():
    """演示速率限制器的使用"""
    print("=== YFinance Rate Limiter Demo ===")
    
    # 显示当前配置
    status = get_rate_limiter().get_status()
    print(f"Current configuration: {status}")
    
    # 配置更严格的限制进行演示
    print("\n🔧 Configuring stricter rate limit for demo (5 requests per minute)...")
    configure_yfinance_rate_limit(5)
    
    # 模拟一些请求
    print("\n📡 Simulating requests...")
    for i in range(7):
        print(f"Request {i+1}:")
        status_before = get_rate_limit_status()
        print(f"  Before: {status_before['available_requests']} requests available")
        
        wait_if_needed()  # 这里会在需要时等待
        
        status_after = get_rate_limit_status()
        print(f"  After: {status_after['available_requests']} requests available")
        print()
    
    print("Demo completed!")


if __name__ == "__main__":
    demo_rate_limiter() 