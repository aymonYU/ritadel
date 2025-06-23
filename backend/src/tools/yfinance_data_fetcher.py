#!/usr/bin/env python3
"""
统一的 YFinance 数据获取器

这个模块提供了统一的数据获取接口，包含：
- 智能速率限制
- 会话管理和代理支持
- 数据缓存和复用
- 批量获取优化
- 强化反检测机制
"""

import os
import time
import random
import threading
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd

import yfinance as yf
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 尝试导入 curl_cffi
try:
    from curl_cffi import requests as cf_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    cf_requests = None

def generate_dynamic_user_agent():
    """生成动态User-Agent，基于真实浏览器模式"""
    # 时间戳和随机ID
    timestamp = str(int(time.time()))
    random_id = str(uuid.uuid4())[:8]
    hash_suffix = hashlib.md5(f"{timestamp}-{random_id}".encode()).hexdigest()[:6]
    
    # 最新Chrome版本
    chrome_versions = [
        "119.0.0.0", "120.0.0.0", "121.0.0.0", "122.0.0.0", "123.0.0.0"
    ]
    chrome_version = random.choice(chrome_versions)
    
    # 操作系统选择
    os_options = [
        "Windows NT 10.0; Win64; x64",
        "Macintosh; Intel Mac OS X 10_15_7",
        "X11; Linux x86_64"
    ]
    os_string = random.choice(os_options)
    
    # 生成更真实的User-Agent
    user_agents = [
        f"Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36",
        f"Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36 Edg/119.0.0.0",
        f"Mozilla/5.0 ({os_string}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    ]
    
    return random.choice(user_agents)

def get_enhanced_headers():
    """获取增强的浏览器headers，完全模拟真实浏览器"""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Pragma': 'no-cache',
    }

@dataclass
class YFinanceDataset:
    """YFinance 数据集合"""
    ticker: str
    info: Dict[str, Any]
    history: pd.DataFrame
    financials: pd.DataFrame
    balance_sheet: pd.DataFrame
    cashflow: pd.DataFrame
    quarterly_financials: pd.DataFrame
    quarterly_balance_sheet: pd.DataFrame
    quarterly_cashflow: pd.DataFrame
    income_stmt: pd.DataFrame
    quarterly_income_stmt: pd.DataFrame
    news: List[Dict[str, Any]]
    fetch_timestamp: float


# Global data cache (简单的内存缓存)
_data_cache: Dict[str, YFinanceDataset] = {}
_cache_lock = threading.Lock()


def get_proxy_list():
    """获取代理列表，支持多种格式"""
    proxies = []
    
    # 从环境变量获取代理
    proxy_http = os.environ.get("YFINANCE_PROXY_HTTP", "")
    proxy_https = os.environ.get("YFINANCE_PROXY_HTTPS", "")
    
    # 解析逗号分隔的代理列表
    if proxy_http:
        for proxy in proxy_http.split(','):
            proxy = proxy.strip()
            if proxy:
                proxies.append({'http': proxy, 'https': proxy})
    
    if proxy_https and proxy_https != proxy_http:
        for proxy in proxy_https.split(','):
            proxy = proxy.strip()
            if proxy:
                proxies.append({'http': proxy, 'https': proxy})
    
    return proxies

def create_yfinance_session():
    """Create a session with enhanced anti-detection features."""
    
    # 在云服务器环境下强制使用代理
    use_proxy = True
    
    if CURL_CFFI_AVAILABLE:
        # 使用curl_cffi，更好的反检测能力
        session = cf_requests.Session()
        
        # 设置动态headers
        enhanced_headers = get_enhanced_headers()
        enhanced_headers['User-Agent'] = generate_dynamic_user_agent()
        session.headers.update(enhanced_headers)
        
        # 代理配置
        if use_proxy:
            proxy_list = get_proxy_list()
            if proxy_list:
                selected_proxy = random.choice(proxy_list)
                session.proxies = selected_proxy
                print(f"🔗 Using proxy: {selected_proxy}")
            else:
                print("⚠️ No proxy available, using direct connection (may fail)")
        
        return session
    else:
        # Fallback to regular requests session
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置动态headers
        enhanced_headers = get_enhanced_headers()
        enhanced_headers['User-Agent'] = generate_dynamic_user_agent()
        session.headers.update(enhanced_headers)
        
        # 代理配置
        if use_proxy:
            proxy_list = get_proxy_list()
            if proxy_list:
                selected_proxy = random.choice(proxy_list)
                session.proxies.update(selected_proxy)
                print(f"🔗 Using proxy: {selected_proxy}")
            else:
                print("⚠️ No proxy available, using direct connection (may fail)")
        
        return session

def safe_fetch_yfinance_data(ticker_symbol: str, max_retries: int = 5) -> Optional[YFinanceDataset]:
    """安全地获取 YFinance 数据，增强重试机制"""
    
    for attempt in range(max_retries):
        try:
            
            # 每次尝试都使用新的session和代理
            session = create_yfinance_session()
            ticker = yf.Ticker(ticker_symbol, session=session)
            
            # 获取所有需要的数据
            print(f"🔄 Fetching data for {ticker_symbol} (attempt {attempt + 1}/{max_retries})")
            
            # Get info and history
            info = ticker.info or {}
            
            # Get historical data (last 1 year)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            history = ticker.history(start=start_date, end=end_date)
            
            # Get financial statements
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow = ticker.cashflow
            quarterly_financials = ticker.quarterly_financials
            quarterly_balance_sheet = ticker.quarterly_balance_sheet
            quarterly_cashflow = ticker.quarterly_cashflow
            
            # Get income statements (same as financials for compatibility)
            income_stmt = financials  # alias
            quarterly_income_stmt = quarterly_financials  # alias
            
            # Get news
            try:
                news = ticker.news or []
            except:
                news = []
            
            # Create dataset
            dataset = YFinanceDataset(
                ticker=ticker_symbol,
                info=info,
                history=history,
                financials=financials,
                balance_sheet=balance_sheet,
                cashflow=cashflow,
                quarterly_financials=quarterly_financials,
                quarterly_balance_sheet=quarterly_balance_sheet,
                quarterly_cashflow=quarterly_cashflow,
                income_stmt=income_stmt,
                quarterly_income_stmt=quarterly_income_stmt,
                news=news,
                fetch_timestamp=time.time()
            )
            
            # 成功后增加随机延迟
            delay = random.uniform(1.0, 3.0)  # 增加延迟时间
            print(f"✅ Successfully fetched {ticker_symbol}, waiting {delay:.1f}s...")
            time.sleep(delay)
            
            return dataset
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ Attempt {attempt + 1} failed for {ticker_symbol}: {str(e)}")
            
            # 检查是否是速率限制错误
            if "too many requests" in error_msg or "rate limit" in error_msg:
                if attempt < max_retries - 1:
                    # 速率限制错误，等待更长时间
                    wait_time = (30 * (attempt + 1)) + random.uniform(10, 30)
                    print(f"⏳ Rate limited, waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                    continue
            
            if attempt < max_retries - 1:
                # 其他错误，指数退避
                wait_time = (2 ** attempt) + random.uniform(5, 15)
                print(f"⏳ Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"💀 All attempts failed for {ticker_symbol}")
                return None
    
    return None

def get_yfinance_data(ticker: str, force_refresh: bool = False) -> Optional[YFinanceDataset]:
    """获取 YFinance 数据，带缓存
    
    Args:
        ticker: 股票代码
        force_refresh: 是否强制刷新（忽略缓存）
        
    Returns:
        YFinance 数据集，如果失败返回 None
    """
    with _cache_lock:
        # 检查缓存
        if not force_refresh and ticker in _data_cache:
            cached_data = _data_cache[ticker]
            # 检查缓存是否过期（5分钟）
            if time.time() - cached_data.fetch_timestamp < 300:
                print(f"Using cached data for {ticker}")
                return cached_data
        
        # 获取新数据
        print(f"Fetching fresh data for {ticker}")
        dataset = safe_fetch_yfinance_data(ticker)
        
        if dataset:
            # 缓存数据
            _data_cache[ticker] = dataset
            
        return dataset

def get_batch_yfinance_data(tickers: List[str], force_refresh: bool = False) -> Dict[str, YFinanceDataset]:
    """批量获取 YFinance 数据
    
    Args:
        tickers: 股票代码列表
        force_refresh: 是否强制刷新
        
    Returns:
        ticker 到数据集的映射
    """
    results = {}
    
    for ticker in tickers:
        try:
            dataset = get_yfinance_data(ticker, force_refresh)
            if dataset:
                results[ticker] = dataset
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
    
    return results

def clear_cache():
    """清除缓存"""
    with _cache_lock:
        _data_cache.clear()
        print("YFinance data cache cleared")

def get_cache_status():
    """获取缓存状态"""
    with _cache_lock:
        return {
            "cached_tickers": list(_data_cache.keys()),
            "cache_size": len(_data_cache),
            "oldest_data_age": min([time.time() - data.fetch_timestamp for data in _data_cache.values()]) if _data_cache else 0
        }

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
    cache_status = get_cache_status()
    print(f"\nCache status: {cache_status}") 