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
    clear_cache as clear_yfinance_cache,
    get_cache_status as get_yfinance_cache_status
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




