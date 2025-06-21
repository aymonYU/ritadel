"""
Proxy Manager Module

这个模块提供了代理池管理功能，支持多代理轮换、故障转移和负载均衡。

主要功能：
- 代理池管理
- 随机代理选择
- 故障检测和自动切换
- 代理状态监控
"""

import os
import random
from typing import Dict, List, Optional, Set


class ProxyManager:
    """代理管理器，支持代理池和故障转移"""
    
    def __init__(self):
        """初始化代理管理器"""
        self.http_proxies = self._parse_proxy_list(os.environ.get("YFINANCE_PROXY_HTTP"))
        self.https_proxies = self._parse_proxy_list(os.environ.get("YFINANCE_PROXY_HTTPS"))
        self.failed_proxies: Set[str] = set()  # 记录失败的代理
    
    def _parse_proxy_list(self, proxy_string: Optional[str]) -> List[str]:
        """解析代理字符串为列表
        
        Args:
            proxy_string: 逗号分隔的代理地址字符串
            
        Returns:
            代理地址列表
        """
        if not proxy_string:
            return []
        return [p.strip() for p in proxy_string.split(',') if p.strip()]
    
    def _format_proxy_url(self, proxy: str, protocol: str = 'http') -> str:
        """格式化代理URL
        
        Args:
            proxy: 代理地址
            protocol: 协议类型 ('http' 或 'https')
            
        Returns:
            格式化后的代理URL
        """
        if not proxy.startswith('http'):
            return f"{protocol}://{proxy}"
        return proxy
    
    def get_proxy_configuration(self) -> Optional[Dict[str, str]]:
        """获取可用的代理配置
        
        Returns:
            代理配置字典，如果没有可用代理则返回None
        """
        proxies = {}
        
        # 选择HTTP代理
        if self.http_proxies:
            available_http = [p for p in self.http_proxies if p not in self.failed_proxies]
            if available_http:
                selected_http = random.choice(available_http)
                proxies['http'] = self._format_proxy_url(selected_http, 'http')
            elif self.http_proxies:  # 如果所有代理都失败了，重置失败列表并重试
                print("⚠️ All HTTP proxies failed, resetting failure list...")
                self.failed_proxies = set()
                selected_http = random.choice(self.http_proxies)
                proxies['http'] = self._format_proxy_url(selected_http, 'http')
        
        # 选择HTTPS代理
        if self.https_proxies:
            available_https = [p for p in self.https_proxies if p not in self.failed_proxies]
            if available_https:
                selected_https = random.choice(available_https)
                proxies['https'] = self._format_proxy_url(selected_https, 'https')
            elif self.https_proxies:  # 如果所有代理都失败了，重置失败列表并重试
                print("⚠️ All HTTPS proxies failed, resetting failure list...")
                self.failed_proxies = set()
                selected_https = random.choice(self.https_proxies)
                proxies['https'] = self._format_proxy_url(selected_https, 'https')
        
        return proxies if proxies else None
    
    def mark_proxy_failed(self, proxy_url: str) -> None:
        """标记代理为失败状态
        
        Args:
            proxy_url: 失败的代理URL
        """
        # 提取代理地址（去掉协议前缀）
        proxy_addr = proxy_url.replace('http://', '').replace('https://', '')
        self.failed_proxies.add(proxy_addr)
        print(f"❌ Marked proxy as failed: {proxy_addr}")
    
    def reset_failed_proxies(self) -> None:
        """重置失败代理列表"""
        self.failed_proxies.clear()
        print("✅ Failed proxy list has been reset")
    
    def get_status(self) -> Dict[str, int]:
        """获取代理池状态
        
        Returns:
            包含代理池状态信息的字典
        """
        return {
            "http_proxies": len(self.http_proxies),
            "https_proxies": len(self.https_proxies),
            "failed_proxies": len(self.failed_proxies),
            "available_http": len([p for p in self.http_proxies if p not in self.failed_proxies]),
            "available_https": len([p for p in self.https_proxies if p not in self.failed_proxies])
        }
    
    def reload_from_env(self) -> None:
        """从环境变量重新加载代理配置"""
        self.http_proxies = self._parse_proxy_list(os.environ.get("YFINANCE_PROXY_HTTP"))
        self.https_proxies = self._parse_proxy_list(os.environ.get("YFINANCE_PROXY_HTTPS"))
        self.failed_proxies.clear()
        print("✅ Proxy configuration reloaded from environment variables")


# 全局代理管理器
_proxy_manager = ProxyManager()


def get_proxy_configuration() -> Optional[Dict[str, str]]:
    """获取代理配置，支持代理池随机选择
    
    Returns:
        代理配置字典，如果没有可用代理则返回None
    """
    return _proxy_manager.get_proxy_configuration()


def mark_proxy_failed(proxy_url: str) -> None:
    """标记代理为失败状态
    
    Args:
        proxy_url: 失败的代理URL
    """
    _proxy_manager.mark_proxy_failed(proxy_url)


def get_proxy_status() -> Dict[str, int]:
    """获取代理池状态
    
    Returns:
        包含代理池状态信息的字典
    """
    return _proxy_manager.get_status()


def configure_proxy_pool(http_proxies: Optional[List[str]] = None, 
                        https_proxies: Optional[List[str]] = None) -> None:
    """配置代理池（可选的便捷函数）
    
    Args:
        http_proxies: HTTP代理列表，例如 ['103.152.112.145:80', '20.111.54.16:80']
        https_proxies: HTTPS代理列表
    
    使用环境变量的示例：
    export YFINANCE_PROXY_HTTP="103.152.112.145:80,20.111.54.16:80,45.76.43.67:80"
    export YFINANCE_PROXY_HTTPS="103.152.112.145:80,20.111.54.16:80,45.76.43.67:80"
    """
    global _proxy_manager
    
    if http_proxies:
        os.environ["YFINANCE_PROXY_HTTP"] = ",".join(http_proxies)
    if https_proxies:
        os.environ["YFINANCE_PROXY_HTTPS"] = ",".join(https_proxies)
    
    # 重新初始化代理管理器
    _proxy_manager = ProxyManager()
    
    status = get_proxy_status()
    print(f"✅ Proxy pool configured: {status}")


def reset_proxy_failures() -> None:
    """重置代理失败列表"""
    _proxy_manager.reset_failed_proxies()


def reload_proxy_config() -> None:
    """从环境变量重新加载代理配置"""
    _proxy_manager.reload_from_env()


def demo_proxy_usage():
    """代理使用示例"""
    print("=== 代理池配置示例 ===")
    
    # 方法1: 使用环境变量
    print("方法1 - 环境变量配置:")
    print('export YFINANCE_PROXY_HTTP="103.152.112.145:80,20.111.54.16:80,45.76.43.67:80"')
    print('export YFINANCE_PROXY_HTTPS="103.152.112.145:80,20.111.54.16:80,45.76.43.67:80"')
    print()
    
    # 方法2: 使用函数配置
    print("方法2 - 程序配置:")
    print("configure_proxy_pool(")
    print("    http_proxies=['103.152.112.145:80', '20.111.54.16:80', '45.76.43.67:80'],")
    print("    https_proxies=['103.152.112.145:80', '20.111.54.16:80', '45.76.43.67:80']")
    print(")")
    print()
    
    # 显示当前状态
    status = get_proxy_status()
    print(f"当前代理池状态: {status}")
    
    if status['http_proxies'] > 0 or status['https_proxies'] > 0:
        print("\n=== 代理测试 ===")
        config = get_proxy_configuration()
        if config:
            print(f"当前选择的代理: {config}")
        else:
            print("未配置代理")


if __name__ == "__main__":
    demo_proxy_usage() 