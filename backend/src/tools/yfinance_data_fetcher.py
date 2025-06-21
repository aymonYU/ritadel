"""
YFinance Data Fetcher Module

这个模块提供统一的 yfinance 数据获取功能，避免重复请求相同的数据。

主要功能：
- 统一的数据获取接口
- 智能缓存和复用
- 支持批量数据获取
- 避免重复的 API 调用
"""

import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .rate_limiter import wait_if_needed
from .proxy_manager import get_proxy_configuration, mark_proxy_failed
import yfinance as yf
import random

# Optional curl_cffi import for better compatibility with anti-bot measures
try:
    from curl_cffi import requests as cf_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    cf_requests = None

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests


@dataclass
class YFinanceDataSet:
    """YFinance 完整数据集"""
    ticker: str
    info: Dict[str, Any]
    financials: Any  # DataFrame
    balance_sheet: Any  # DataFrame
    cashflow: Any  # DataFrame
    quarterly_financials: Any  # DataFrame
    quarterly_balance_sheet: Any  # DataFrame
    quarterly_cashflow: Any  # DataFrame
    income_stmt: Any  # DataFrame
    quarterly_income_stmt: Any  # DataFrame
    fetch_timestamp: float
    
    def is_fresh(self, max_age_seconds: int = 3600) -> bool:
        """检查数据是否仍然新鲜（默认1小时内）"""
        return (time.time() - self.fetch_timestamp) < max_age_seconds


class YFinanceDataFetcher:
    """统一的 YFinance 数据获取器"""
    
    def __init__(self):
        self._data_cache: Dict[str, YFinanceDataSet] = {}
        self._user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
    
    def _create_session(self, use_proxy=False):
        """创建 HTTP 会话
        
        Args:
            use_proxy: 是否使用代理，默认为 False（优先直连）
        """
        # 选择会话类型
        if CURL_CFFI_AVAILABLE:
            session = cf_requests.Session()
        else:
            session = requests.Session()
            # 只有标准 requests 需要重试策略配置
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        
        # 通用配置：用户代理
        session.headers.update({
            'User-Agent': random.choice(self._user_agents)
        })
        
        # 代理配置：只有在明确要求使用代理时才配置
        if use_proxy:
            proxy_config = get_proxy_configuration()
            if proxy_config:
                if CURL_CFFI_AVAILABLE:
                    session.proxies = proxy_config
                else:
                    session.proxies.update(proxy_config)
                print(f"🔗 Using proxy configuration: {proxy_config}")
            else:
                print("⚠️ Proxy requested but no proxy configuration available")
        else:
            print("🌐 Using direct connection (no proxy)")
        
        return session
    
    def _safe_request(self, ticker: str, max_retries: int = 3) -> YFinanceDataSet:
        """安全地获取 YFinance 数据，包含重试逻辑
        
        策略：
        1. 第一次尝试：使用直连（不使用代理）
        2. 第一次失败后：启用代理重试
        3. 代理失败：尝试其他代理
        """
        last_exception = None
        use_proxy = False  # 默认不使用代理，优先直连
        used_proxy_config = None
        
        for attempt in range(max_retries):
            try:
                # 应用速率限制
                wait_if_needed()
                
                # 第一次失败后，启用代理
                if attempt > 0 and not use_proxy:
                    use_proxy = True
                    print(f"💡 First attempt failed, enabling proxy for retry {attempt + 1}")
                
                # 创建会话
                session = self._create_session(use_proxy=use_proxy)
                
                # 记录当前使用的代理配置（用于失败时标记）
                if use_proxy:
                    used_proxy_config = get_proxy_configuration()
                else:
                    used_proxy_config = None
                
                # 创建 ticker 对象
                yf_ticker = yf.Ticker(ticker, session=session)
                
                # 一次性获取所有需要的数据
                connection_type = "proxy" if use_proxy else "direct"
                print(f"📡 Fetching comprehensive data for {ticker} via {connection_type} connection...")
                
                # 获取基本信息
                info = yf_ticker.info
                
                # 获取财务报表数据
                financials = yf_ticker.financials
                balance_sheet = yf_ticker.balance_sheet
                cashflow = yf_ticker.cashflow
                quarterly_financials = yf_ticker.quarterly_financials
                quarterly_balance_sheet = yf_ticker.quarterly_balance_sheet
                quarterly_cashflow = yf_ticker.quarterly_cashflow
                
                # 获取损益表数据（新版本 yfinance 的属性）
                try:
                    income_stmt = yf_ticker.income_stmt
                    quarterly_income_stmt = yf_ticker.quarterly_income_stmt
                except AttributeError:
                    # 如果新属性不存在，使用旧的属性名
                    income_stmt = financials
                    quarterly_income_stmt = quarterly_financials
                
                # 创建数据集对象
                dataset = YFinanceDataSet(
                    ticker=ticker,
                    info=info,
                    financials=financials,
                    balance_sheet=balance_sheet,
                    cashflow=cashflow,
                    quarterly_financials=quarterly_financials,
                    quarterly_balance_sheet=quarterly_balance_sheet,
                    quarterly_cashflow=quarterly_cashflow,
                    income_stmt=income_stmt,
                    quarterly_income_stmt=quarterly_income_stmt,
                    fetch_timestamp=time.time()
                )
                
                # 添加随机延迟以避免被检测为机器人
                time.sleep(random.uniform(0.1, 0.5))
                
                success_method = "proxy" if use_proxy else "direct connection"
                print(f"✅ Successfully fetched data for {ticker} via {success_method}")
                return dataset
                
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                
                # 检查是否是代理相关的错误
                proxy_errors = ['proxy', 'connection', 'timeout', 'unreachable', 'refused']
                is_proxy_error = any(error_type in error_msg for error_type in proxy_errors)
                
                # 如果使用了代理且出现代理相关错误，标记代理为失败
                if use_proxy and is_proxy_error and used_proxy_config:
                    for protocol, proxy_url in used_proxy_config.items():
                        mark_proxy_failed(proxy_url)
                    print(f"🔄 Proxy error detected, will try another proxy for next attempt")
                elif not use_proxy:
                    print(f"🔄 Direct connection failed, will try with proxy for next attempt")
                
                attempt_method = "proxy" if use_proxy else "direct connection"
                print(f"❌ Attempt {attempt + 1}/{max_retries} via {attempt_method} failed for {ticker}: {str(e)}")
                
                # 如果不是最后一次尝试，则等待后重试
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"⏳ Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
        
        # 所有重试都失败了，抛出最后一个异常
        print(f"💀 All {max_retries} attempts failed for {ticker}")
        raise last_exception
    
    def get_data(self, ticker: str, force_refresh: bool = False, max_age_seconds: int = 3600) -> YFinanceDataSet:
        """获取 ticker 的完整数据集
        
        Args:
            ticker: 股票代码
            force_refresh: 是否强制刷新数据
            max_age_seconds: 缓存数据的最大年龄（秒）
            
        Returns:
            YFinanceDataSet: 完整的财务数据集
        """
        # 检查缓存
        if not force_refresh and ticker in self._data_cache:
            cached_data = self._data_cache[ticker]
            if cached_data.is_fresh(max_age_seconds):
                print(f"📋 Using cached data for {ticker}")
                return cached_data
        
        # 获取新数据
        dataset = self._safe_request(ticker)
        
        # 缓存数据
        self._data_cache[ticker] = dataset
        
        return dataset
    
    def get_batch_data(self, tickers: list[str], force_refresh: bool = False, max_age_seconds: int = 3600) -> Dict[str, YFinanceDataSet]:
        """批量获取多个 ticker 的数据
        
        Args:
            tickers: 股票代码列表
            force_refresh: 是否强制刷新数据
            max_age_seconds: 缓存数据的最大年龄（秒）
            
        Returns:
            Dict[str, YFinanceDataSet]: ticker 到数据集的映射
        """
        results = {}
        
        for ticker in tickers:
            try:
                results[ticker] = self.get_data(ticker, force_refresh, max_age_seconds)
            except Exception as e:
                print(f"❌ Failed to fetch data for {ticker}: {str(e)}")
                # 继续处理其他 ticker
                continue
        
        return results
    
    def clear_cache(self, ticker: Optional[str] = None):
        """清除缓存
        
        Args:
            ticker: 要清除的特定 ticker，如果为 None 则清除所有缓存
        """
        if ticker:
            self._data_cache.pop(ticker, None)
            print(f"🗑️ Cleared cache for {ticker}")
        else:
            self._data_cache.clear()
            print("🗑️ Cleared all cache")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        return {
            "cached_tickers": list(self._data_cache.keys()),
            "cache_size": len(self._data_cache),
            "cache_details": {
                ticker: {
                    "fetch_timestamp": dataset.fetch_timestamp,
                    "age_seconds": time.time() - dataset.fetch_timestamp,
                    "is_fresh": dataset.is_fresh()
                }
                for ticker, dataset in self._data_cache.items()
            }
        }


# 全局数据获取器实例
_data_fetcher = YFinanceDataFetcher()


def get_yfinance_data(ticker: str, force_refresh: bool = False, max_age_seconds: int = 3600) -> YFinanceDataSet:
    """获取 YFinance 数据的便捷函数
    
    Args:
        ticker: 股票代码
        force_refresh: 是否强制刷新数据
        max_age_seconds: 缓存数据的最大年龄（秒）
        
    Returns:
        YFinanceDataSet: 完整的财务数据集
    """
    return _data_fetcher.get_data(ticker, force_refresh, max_age_seconds)


def get_batch_yfinance_data(tickers: list[str], force_refresh: bool = False, max_age_seconds: int = 3600) -> Dict[str, YFinanceDataSet]:
    """批量获取 YFinance 数据的便捷函数
    
    Args:
        tickers: 股票代码列表
        force_refresh: 是否强制刷新数据
        max_age_seconds: 缓存数据的最大年龄（秒）
        
    Returns:
        Dict[str, YFinanceDataSet]: ticker 到数据集的映射
    """
    return _data_fetcher.get_batch_data(tickers, force_refresh, max_age_seconds)


def clear_yfinance_cache(ticker: Optional[str] = None):
    """清除 YFinance 数据缓存
    
    Args:
        ticker: 要清除的特定 ticker，如果为 None 则清除所有缓存
    """
    _data_fetcher.clear_cache(ticker)


def get_yfinance_cache_status() -> Dict[str, Any]:
    """获取 YFinance 缓存状态"""
    return _data_fetcher.get_cache_status()


if __name__ == "__main__":
    # 演示用法
    print("=== YFinance Data Fetcher Demo ===")
    
    # 获取单个股票数据
    try:
        data = get_yfinance_data("AAPL")
        print(f"✅ Fetched data for AAPL")
        print(f"   Market Cap: {data.info.get('marketCap', 'N/A')}")
        print(f"   Data age: {time.time() - data.fetch_timestamp:.1f} seconds")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 显示缓存状态
    cache_status = get_yfinance_cache_status()
    print(f"\nCache status: {cache_status}") 