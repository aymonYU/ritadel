#!/usr/bin/env python3
"""
优化后的 YFinance API 使用示例
Optimized YFinance API Usage Example

这个文件演示了如何使用新的统一数据获取器来避免重复的 API 调用。
"""

import os
import sys
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from tools import (
    # 新的优化函数
    get_comprehensive_data,
    get_batch_comprehensive_data,
    
    # 统一数据获取器
    get_yfinance_data,
    get_batch_yfinance_data,
    get_yfinance_cache_status,
    clear_yfinance_cache,
    
    # 传统函数（现在内部已优化）
    get_financial_metrics,
    search_line_items,
    get_market_cap,
    
    # 工具配置
    setup_tools,
    get_tools_status
)


def demo_single_stock_optimization():
    """演示单个股票的优化获取方法"""
    print("=" * 60)
    print("📊 单个股票数据获取优化演示")
    print("=" * 60)
    
    ticker = "AAPL"
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 方法1: 使用新的综合数据获取函数（推荐）
    print("\n🚀 方法1: 使用 get_comprehensive_data（一次获取所有数据）")
    print("-" * 50)
    
    line_items_needed = [
        "revenue", "net_income", "earnings_per_share", 
        "free_cash_flow", "total_assets", "total_debt"
    ]
    
    comprehensive_data = get_comprehensive_data(
        ticker=ticker,
        end_date=end_date,
        period="ttm",
        limit=5,
        include_line_items=line_items_needed
    )
    
    if comprehensive_data.get("financial_metrics"):
        metrics = comprehensive_data["financial_metrics"][0]
        print(f"✅ 获取到 {ticker} 的综合数据:")
        print(f"   💰 市值: ${metrics.market_cap:,.0f}" if metrics.market_cap else "   💰 市值: N/A")
        print(f"   📊 P/E 比率: {metrics.price_to_earnings_ratio:.2f}" if metrics.price_to_earnings_ratio else "   📊 P/E 比率: N/A")
        print(f"   📈 ROE: {metrics.return_on_equity:.2%}" if metrics.return_on_equity else "   📈 ROE: N/A")
        print(f"   📋 财务指标数量: {len(comprehensive_data['financial_metrics'])}")
        print(f"   🔢 Line items 数量: {len(comprehensive_data['line_items'])}")
        print(f"   ⏱️ 数据年龄: {comprehensive_data['data_age_seconds']:.1f} 秒")
    
    # 方法2: 传统方法（现在内部已优化，会复用数据）
    print("\n🔄 方法2: 传统方法（现在内部已优化，会复用缓存的数据）")
    print("-" * 50)
    
    # 这些调用现在会复用之前获取的数据，不会重复请求 API
    financial_metrics = get_financial_metrics(ticker, end_date, limit=3)
    line_items = search_line_items(ticker, line_items_needed, end_date, limit=3)
    market_cap = get_market_cap(ticker, end_date)
    
    print(f"✅ 传统方法获取结果:")
    print(f"   📊 财务指标: {len(financial_metrics)} 条")
    print(f"   🔢 Line items: {len(line_items)} 条")
    print(f"   💰 市值: ${market_cap:,.0f}" if market_cap else "   💰 市值: N/A")
    
    # 显示缓存状态
    cache_status = get_yfinance_cache_status()
    print(f"\n📋 缓存状态: {cache_status['cache_size']} 个股票已缓存")


def demo_batch_optimization():
    """演示批量股票数据获取优化"""
    print("\n" + "=" * 60)
    print("📈 批量股票数据获取优化演示")
    print("=" * 60)
    
    tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    common_line_items = [
        "revenue", "net_income", "total_assets", 
        "free_cash_flow", "debt_to_equity"
    ]
    
    print(f"\n🚀 批量获取 {len(tickers)} 个股票的数据...")
    print(f"股票列表: {', '.join(tickers)}")
    
    # 使用优化的批量获取函数
    batch_data = get_batch_comprehensive_data(
        tickers=tickers,
        end_date=end_date,
        period="ttm",
        limit=3,
        common_line_items=common_line_items
    )
    
    print(f"\n✅ 批量获取完成！结果汇总:")
    print("-" * 40)
    
    for ticker, data in batch_data.items():
        if data.get("financial_metrics"):
            metrics = data["financial_metrics"][0]
            market_cap = metrics.market_cap
            pe_ratio = metrics.price_to_earnings_ratio
            
            print(f"{ticker:>6}: 市值 ${market_cap/1e9:.1f}B" if market_cap else f"{ticker:>6}: 市值 N/A", end="")
            print(f", P/E {pe_ratio:.1f}" if pe_ratio else ", P/E N/A", end="")
            print(f", 数据年龄 {data.get('data_age_seconds', 0):.1f}s")
        else:
            error = data.get("error", "未知错误")
            print(f"{ticker:>6}: ❌ 获取失败 - {error}")


def demo_cache_management():
    """演示缓存管理功能"""
    print("\n" + "=" * 60)
    print("🗂️ 缓存管理演示")
    print("=" * 60)
    
    # 显示当前缓存状态
    cache_status = get_yfinance_cache_status()
    print(f"\n📊 当前缓存状态:")
    print(f"   缓存的股票数量: {cache_status['cache_size']}")
    print(f"   缓存的股票: {', '.join(cache_status['cached_tickers'])}")
    
    if cache_status['cache_details']:
        print(f"\n📋 缓存详情:")
        for ticker, details in cache_status['cache_details'].items():
            is_fresh = "🟢 新鲜" if details['is_fresh'] else "🔴 过期"
            print(f"   {ticker}: {is_fresh}, 年龄 {details['age_seconds']:.1f}s")
    
    # 演示清除特定缓存
    if cache_status['cached_tickers']:
        first_ticker = cache_status['cached_tickers'][0]
        print(f"\n🗑️ 清除 {first_ticker} 的缓存...")
        clear_yfinance_cache(first_ticker)
        
        updated_status = get_yfinance_cache_status()
        print(f"   清除后缓存数量: {updated_status['cache_size']}")


def demo_tools_status():
    """演示工具状态监控"""
    print("\n" + "=" * 60)
    print("🔧 工具状态监控演示")
    print("=" * 60)
    
    status = get_tools_status()
    
    print(f"\n📊 整体工具状态:")
    print(f"   ⏱️ 时间戳: {status['timestamp']}")
    
    # 速率限制器状态
    rate_status = status['rate_limiter']
    print(f"\n🚦 速率限制器:")
    print(f"   当前使用量: {rate_status.get('current_usage', 0)}")
    print(f"   限制: {rate_status.get('limit_per_minute', 0)}/分钟")
    
    # 代理管理器状态
    proxy_status = status['proxy_manager']
    print(f"\n🔗 代理管理器:")
    print(f"   HTTP代理池: {len(proxy_status.get('http_proxies', []))}")
    print(f"   HTTPS代理池: {len(proxy_status.get('https_proxies', []))}")
    
    # 数据获取器状态
    data_status = status['data_fetcher']
    print(f"\n📡 数据获取器:")
    print(f"   缓存股票数: {data_status.get('cache_size', 0)}")
    
    if data_status.get('cached_tickers'):
        fresh_count = sum(1 for details in data_status['cache_details'].values() if details['is_fresh'])
        print(f"   新鲜数据: {fresh_count}/{data_status['cache_size']}")


def main():
    """主演示函数"""
    print("🚀 YFinance API 优化使用演示")
    print("=" * 60)
    
    # 配置工具
    print("⚙️ 配置工具...")
    setup_tools(rate_limit_per_minute=20)  # 保守的速率限制
    
    try:
        # 演示单个股票优化
        demo_single_stock_optimization()
        
        # 演示批量优化
        demo_batch_optimization()
        
        # 演示缓存管理
        demo_cache_management()
        
        # 演示工具状态
        demo_tools_status()
        
        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("\n💡 主要优化点:")
        print("   1. 统一数据获取器避免重复 API 调用")
        print("   2. 智能缓存机制复用已获取的数据")
        print("   3. 批量处理减少总体请求次数")
        print("   4. 综合数据函数一次获取多种数据类型")
        print("   5. 向后兼容现有代码，无需大量修改")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 