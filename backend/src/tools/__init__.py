"""
Tools Module

这个模块提供了各种工具函数和类，用于数据获取、限流、代理管理等功能。

主要模块：
- api: 主要的数据获取API
- rate_limiter: 速率限制功能
- proxy_manager: 代理池管理功能
"""

# 导入主要的API函数
from .api import (
    get_financial_metrics,
    search_line_items,
    get_prices,
    get_insider_trades,
    get_company_news,
    get_market_cap,
    prices_to_df,
    get_price_data,
    get_api_keys
)

# 导入限流相关功能
from .rate_limiter import (
    configure_yfinance_rate_limit,
    get_rate_limit_status,
    wait_if_needed,
    reset_rate_limiter,
    get_rate_limiter,
    demo_rate_limiter
)

# 导入代理管理功能
from .proxy_manager import (
    configure_proxy_pool,
    get_proxy_status,
    get_proxy_configuration,
    mark_proxy_failed,
    reset_proxy_failures,
    reload_proxy_config,
    demo_proxy_usage
)

# 导入统一数据获取器功能
from .yfinance_data_fetcher import (
    get_yfinance_data,
    get_batch_yfinance_data,
    clear_yfinance_cache,
    get_yfinance_cache_status
)

# 导入综合数据获取功能（专为 agents 优化）
from .api import (
    get_comprehensive_data,
    get_batch_comprehensive_data
)

__all__ = [
    # API functions
    'get_financial_metrics',
    'search_line_items', 
    'get_prices',
    'get_insider_trades',
    'get_company_news',
    'get_market_cap',
    'prices_to_df',
    'get_price_data',
    'get_api_keys',
    
    # Rate limiter functions
    'configure_yfinance_rate_limit',
    'get_rate_limit_status',
    'wait_if_needed',
    'reset_rate_limiter',
    'get_rate_limiter',
    'demo_rate_limiter',
    
    # Proxy manager functions
    'configure_proxy_pool',
    'get_proxy_status',
    'get_proxy_configuration',
    'mark_proxy_failed',
    'reset_proxy_failures',
    'reload_proxy_config',
    'demo_proxy_usage',
    
    # Unified data fetcher functions
    'get_yfinance_data',
    'get_batch_yfinance_data',
    'clear_yfinance_cache',
    'get_yfinance_cache_status',
    
    # Comprehensive data functions (optimized for agents)
    'get_comprehensive_data',
    'get_batch_comprehensive_data'
]


def setup_tools(rate_limit_per_minute=30, proxy_http_list=None, proxy_https_list=None):
    """一键配置所有工具
    
    Args:
        rate_limit_per_minute: 每分钟请求限制
        proxy_http_list: HTTP代理列表
        proxy_https_list: HTTPS代理列表
    
    Example:
        setup_tools(
            rate_limit_per_minute=20,
            proxy_http_list=['103.152.112.145:80', '20.111.54.16:80'],
            proxy_https_list=['103.152.112.145:80', '20.111.54.16:80']
        )
    """
    print("🔧 Setting up tools...")
    
    # 配置速率限制
    configure_yfinance_rate_limit(rate_limit_per_minute)
    
    # 配置代理池（如果提供）
    if proxy_http_list or proxy_https_list:
        configure_proxy_pool(proxy_http_list, proxy_https_list)
    
    # 显示配置状态
    rate_status = get_rate_limit_status()
    proxy_status = get_proxy_status()
    
    print(f"✅ Tools setup completed!")
    print(f"   Rate limit: {rate_status}")
    print(f"   Proxy status: {proxy_status}")


def get_tools_status():
    """获取所有工具的状态信息
    
    Returns:
        包含所有工具状态的字典
    """
    import time
    return {
        "rate_limiter": get_rate_limit_status(),
        "proxy_manager": get_proxy_status(),
        "data_fetcher": get_yfinance_cache_status(),
        "timestamp": time.time()
    }


def demo_all_tools():
    """演示所有工具的使用方法"""
    print("=" * 50)
    print("🛠️  TOOLS MODULE DEMO")
    print("=" * 50)
    
    print("\n1. 速率限制器演示:")
    demo_rate_limiter()
    
    print("\n" + "=" * 50)
    print("\n2. 代理管理器演示:")
    demo_proxy_usage()
    
    print("\n" + "=" * 50)
    print("\n3. 整体状态:")
    status = get_tools_status()
    print(f"所有工具状态: {status}")


if __name__ == "__main__":
    demo_all_tools() 