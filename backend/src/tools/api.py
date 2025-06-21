import os
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any, Optional
from functools import lru_cache
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading

# Optional curl_cffi import for better compatibility with anti-bot measures
try:
    from curl_cffi import requests as cf_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    cf_requests = None  # 明确设置为 None

from data.cache import get_cache
from data.models import (
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
)

# Import rate limiter and proxy manager
from .rate_limiter import wait_if_needed
from .proxy_manager import get_proxy_configuration, mark_proxy_failed
from .yfinance_data_fetcher import get_yfinance_data

# Global cache instance
_cache = get_cache()


def safe_yfinance_request(ticker_symbol, operation_func, max_retries=3):
    """Safely make yfinance requests with rate limiting and retry logic.
    
    注意：这个函数现在主要用于向后兼容。
    新代码应该使用 get_yfinance_data() 或 get_comprehensive_data()。
    """
    try:
        # 获取统一的数据集
        dataset = get_yfinance_data(ticker_symbol)
        
        # 创建一个模拟的 ticker 对象来兼容现有代码
        class MockTicker:
            def __init__(self, dataset):
                self.info = dataset.info
                self.financials = dataset.financials
                self.balance_sheet = dataset.balance_sheet
                self.cashflow = dataset.cashflow
                self.quarterly_financials = dataset.quarterly_financials
                self.quarterly_balance_sheet = dataset.quarterly_balance_sheet
                self.quarterly_cashflow = dataset.quarterly_cashflow
                self.income_stmt = dataset.income_stmt
                self.quarterly_income_stmt = dataset.quarterly_income_stmt
        
        mock_ticker = MockTicker(dataset)
        return operation_func(mock_ticker)
        
    except Exception as e:
        print(f"Error in safe_yfinance_request for {ticker_symbol}: {str(e)}")
        raise e

# Define API keys and fallback order
def get_api_keys():
    """Get all available API keys with fallback options."""
    return {
        "alpha_vantage": os.environ.get("ALPHA_VANTAGE_API_KEY"),
        "stockdata": os.environ.get("STOCKDATA_API_KEY"),
        "finnhub": os.environ.get("FINNHUB_API_KEY"),
        "eodhd": os.environ.get("EODHD_API_KEY"),
        # 移除了 coingecko 和 cryptocompare API 密钥，因为不再支持加密货币
        # Removed coingecko and cryptocompare API keys as cryptocurrency is no longer supported
        # "coingecko": os.environ.get("COINGECKO_API_KEY"),
        # "cryptocompare": os.environ.get("CRYPTOCOMPARE_API_KEY"),
    }

# is_crypto 参数已移除，此函数现在只获取股票价格
# is_crypto parameter removed, this function now only fetches stock prices
def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data with multi-source fallback strategy."""
    # Check cache first
    # cache_key 更新为只使用 ticker，移除了加密货币相关的 cache_key 逻辑
    # cache_key updated to only use ticker, removed crypto-related cache_key logic
    cache_key = ticker 
    if cached_data := _cache.get_prices(cache_key):
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    # 移除了 is_crypto 条件判断和 get_crypto_prices 的调用
    # Removed is_crypto conditional check and call to get_crypto_prices
    # if is_crypto:
    #     return get_crypto_prices(ticker, start_date, end_date)
    
    
    # Fallback to StockData.org if Yahoo fails
    try:
        api_keys = get_api_keys()
        if api_key := api_keys.get("stockdata"):
            url = f"https://api.stockdata.org/v1/data/eod?symbols={ticker}&date_from={start_date}&date_to={end_date}&api_key={api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    prices = []
                    for item in data["data"]:
                        price = Price(
                            open=float(item["open"]),
                            close=float(item["close"]),
                            high=float(item["high"]),
                            low=float(item["low"]),
                            volume=int(item["volume"]),
                            time=item["date"]
                        )
                        prices.append(price)
                    
                    # Cache the results
                    _cache.set_prices(cache_key, [p.model_dump() for p in prices])
                    return prices
    except Exception as e:
        print(f"StockData.org error for {ticker}: {str(e)}")
        
    # Last resort: Alpha Vantage
    try:
        api_keys = get_api_keys()
        if api_key := api_keys.get("alpha_vantage"):
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if "Time Series (Daily)" in data:
                    time_series = data["Time Series (Daily)"]
                    prices = []
                    
                    for date, values in time_series.items():
                        if start_date <= date <= end_date:
                            price = Price(
                                open=float(values["1. open"]),
                                close=float(values["4. close"]),
                                high=float(values["2. high"]),
                                low=float(values["3. low"]),
                                volume=int(values["6. volume"]),
                                time=date
                            )
                            prices.append(price)
                    
                    # Sort by date, newest first
                    prices.sort(key=lambda x: x.time, reverse=True)
                    
                    # Cache the results
                    _cache.set_prices(cache_key, [p.model_dump() for p in prices])
                    return prices
    except Exception as e:
        print(f"Alpha Vantage error for {ticker}: {str(e)}")
    
    # Return empty list if all sources fail
    return []

def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10
) -> list[FinancialMetrics]:
    """Fetch financial metrics from cache or APIs."""
    print(f"Fetching financial metrics for {ticker} on {end_date}")

    if cached_data := _cache.get_financial_metrics(ticker):
        # Filter cached data by date and limit
        # 按报告期间过滤缓存数据并限制数量
        # report_period: 财务报告的期间日期，用于标识财务数据的报告时间
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    # If not in cache or insufficient data, fetch from Yahoo Finance using unified data fetcher
    try:
        # 使用统一的数据获取器
        yf_dataset = get_yfinance_data(ticker)
        
        # Extract data from the dataset
        info = yf_dataset.info
        financial_data = yf_dataset.financials
        balance_sheet = yf_dataset.balance_sheet
        cash_flow = yf_dataset.cashflow
        quarterly_financials = yf_dataset.quarterly_financials
        quarterly_balance_sheet = yf_dataset.quarterly_balance_sheet
        quarterly_cashflow = yf_dataset.quarterly_cashflow
        
        # Combine data sources based on available dates
        all_dates = set()
        for df in [financial_data, balance_sheet, cash_flow, 
                  quarterly_financials, quarterly_balance_sheet, quarterly_cashflow]:
            if not df.empty:
                all_dates.update(df.columns)
        
        # Sort dates in descending order
        sorted_dates = sorted(all_dates, reverse=True)
        
        # Create financial metrics for each date
        financial_metrics = []
        for i, date in enumerate(sorted_dates):
            if i >= limit:
                break
                
            report_date = date.strftime('%Y-%m-%d')
            if report_date > end_date:
                continue
                
            # Gather metrics that we can calculate
            try:
                # Basic metrics from info
                market_cap = info.get('marketCap')
                enterprise_value = info.get('enterpriseValue')
                
                # Price ratios
                pe_ratio = info.get('trailingPE')
                pb_ratio = info.get('priceToBook')
                ps_ratio = info.get('priceToSalesTrailing12Months')
                
                # Get financial data for this period if available
                net_income = get_value_from_df(financial_data, 'Net Income', date)
                total_revenue = get_value_from_df(financial_data, 'Total Revenue', date)
                
                # 过滤掉没有 net_income 的记录，类似于 search_line_items 中的过滤逻辑
                # Filter out records without net_income, similar to the filtering logic in search_line_items
                if net_income is None:
                    continue
                
                # Balance sheet items
                total_assets = get_value_from_df(balance_sheet, 'Total Assets', date)
                total_liabilities = get_value_from_df(balance_sheet, 'Total Liabilities Net Minority Interest', date)
                total_equity = total_assets - total_liabilities if total_assets and total_liabilities else None
                
                # Cash flow items
                operating_cash_flow = get_value_from_df(cash_flow, 'Operating Cash Flow', date)
                capital_expenditure = get_value_from_df(cash_flow, 'Capital Expenditure', date)
                free_cash_flow = operating_cash_flow + capital_expenditure if operating_cash_flow and capital_expenditure else None
                
                # Calculate derived metrics
                gross_margin = get_value_from_df(financial_data, 'Gross Profit', date) / total_revenue if total_revenue else None
                operating_margin = get_value_from_df(financial_data, 'Operating Income', date) / total_revenue if total_revenue else None
                net_margin = net_income / total_revenue if net_income and total_revenue else None
                
                # Return ratios
                return_on_equity = net_income / total_equity if net_income and total_equity else None
                return_on_assets = net_income / total_assets if net_income and total_assets else None
                
                # Liquidity ratios
                current_assets = get_value_from_df(balance_sheet, 'Current Assets', date)
                current_liabilities = get_value_from_df(balance_sheet, 'Current Liabilities', date)
                current_ratio = current_assets / current_liabilities if current_assets and current_liabilities else None
                
                # Debt ratios
                debt_to_equity = total_liabilities / total_equity if total_liabilities and total_equity else None
                
                # Growth metrics (calculate if previous period available)
                prev_date = sorted_dates[i+1] if i+1 < len(sorted_dates) else None
                if prev_date:
                    prev_revenue = get_value_from_df(financial_data, 'Total Revenue', prev_date)
                    prev_net_income = get_value_from_df(financial_data, 'Net Income', prev_date)
                    
                    revenue_growth = (total_revenue / prev_revenue - 1) if total_revenue and prev_revenue else None
                    earnings_growth = (net_income / prev_net_income - 1) if net_income and prev_net_income else None
                else:
                    revenue_growth = None
                    earnings_growth = None
                
                # Per share values
                shares_outstanding = info.get('sharesOutstanding')
                if shares_outstanding:
                    earnings_per_share = net_income / shares_outstanding if net_income else None
                    book_value_per_share = total_equity / shares_outstanding if total_equity else None
                    free_cash_flow_per_share = free_cash_flow / shares_outstanding if free_cash_flow else None
                else:
                    earnings_per_share = info.get('trailingEps')
                    book_value_per_share = None
                    free_cash_flow_per_share = None
                
                # Create the metrics object
                metrics = FinancialMetrics(
                    ticker=ticker,
                    report_period=report_date,
                    period=period,
                    currency=info.get('currency', 'USD'),
                    market_cap=market_cap,
                    enterprise_value=enterprise_value,
                    price_to_earnings_ratio=pe_ratio,
                    price_to_book_ratio=pb_ratio,
                    price_to_sales_ratio=ps_ratio,
                    enterprise_value_to_ebitda_ratio=info.get('enterpriseToEbitda'),
                    enterprise_value_to_revenue_ratio=enterprise_value / total_revenue if enterprise_value and total_revenue else None,
                    free_cash_flow_yield=free_cash_flow / market_cap if free_cash_flow and market_cap else None,
                    peg_ratio=info.get('pegRatio'),
                    gross_margin=gross_margin,
                    operating_margin=operating_margin,
                    net_margin=net_margin,
                    return_on_equity=return_on_equity,
                    return_on_assets=return_on_assets,
                    return_on_invested_capital=info.get('returnOnAssets'),  # Approximation
                    asset_turnover=total_revenue / total_assets if total_revenue and total_assets else None,
                    inventory_turnover=None,  # Not easily available
                    receivables_turnover=None,  # Not easily available
                    days_sales_outstanding=None,  # Not easily available
                    operating_cycle=None,  # Not easily available
                    working_capital_turnover=None,  # Not easily available
                    current_ratio=current_ratio,
                    quick_ratio=None,  # Not easily available
                    cash_ratio=None,  # Not easily available
                    operating_cash_flow_ratio=operating_cash_flow / current_liabilities if operating_cash_flow and current_liabilities else None,
                    debt_to_equity=debt_to_equity,
                    debt_to_assets=total_liabilities / total_assets if total_liabilities and total_assets else None,
                    interest_coverage=None,  # Not easily available
                    revenue_growth=revenue_growth,
                    earnings_growth=earnings_growth,
                    book_value_growth=None,  # Requires more historical data
                    earnings_per_share_growth=None,  # Requires more historical data
                    free_cash_flow_growth=None,  # Requires more historical data
                    operating_income_growth=None,  # Requires more historical data
                    ebitda_growth=None,  # Requires more historical data
                    payout_ratio=info.get('payoutRatio'),
                    earnings_per_share=earnings_per_share,
                    book_value_per_share=book_value_per_share,
                    free_cash_flow_per_share=free_cash_flow_per_share,
                )
                
                financial_metrics.append(metrics)
                
            except Exception as e:
                print(f"Error processing metrics for {ticker} on {report_date}: {str(e)}")
                continue
        
        # Cache the results
        if financial_metrics:
            _cache.set_financial_metrics(ticker, [m.model_dump() for m in financial_metrics])
        
            
        return financial_metrics
        
    except Exception as e:
        print(f"Error fetching financial metrics for {ticker}: {str(e)}")
        return []

def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10
) -> list[LineItem]:
    """Search financial line items for a ticker."""
    try:
        # 使用统一的数据获取器，复用可能已经获取的数据
        yf_dataset = get_yfinance_data(ticker)
        
        # Extract statements from the dataset
        income_stmt = yf_dataset.income_stmt
        balance_sheet = yf_dataset.balance_sheet
        cash_flow = yf_dataset.cashflow
        q_income_stmt = yf_dataset.quarterly_income_stmt
        q_balance_sheet = yf_dataset.quarterly_balance_sheet
        q_cash_flow = yf_dataset.quarterly_cashflow
        info = yf_dataset.info
        
        # Get all available dates from the statements
        all_dates = set()
        for df in [income_stmt, balance_sheet, cash_flow, 
                   q_income_stmt, q_balance_sheet, q_cash_flow]:
            if hasattr(df, 'columns'):
                all_dates.update(df.columns)
                
        # Sort dates in descending order
        sorted_dates = sorted(all_dates, reverse=True)
        
        # Create line items for each date
        result_items = []
        for i, date in enumerate(sorted_dates):
            if i >= limit:
                break
                
            report_date = date.strftime('%Y-%m-%d')
            if report_date > end_date:
                continue
                
            # Create a base line item with required fields
            line_item_data = {
                "ticker": ticker,
                "report_period": report_date,
                "period": period,
                "currency": info.get('currency', 'USD'),
            }
            
            # Map requested line items to financial statement items
            line_item_mapping = {
                "revenue": ("Total Revenue", income_stmt),
                "net_income": ("Net Income", income_stmt),
                "operating_income": ("Operating Income", income_stmt),
                "gross_margin": (None, None),  # Will calculate from Gross Profit / Revenue
                "operating_margin": (None, None),  # Will calculate from Operating Income / Revenue
                "return_on_invested_capital": (None, None),  # Will calculate
                "free_cash_flow": (None, None),  # Will calculate from OCF - CapEx
                "cash_and_equivalents": ("Cash And Cash Equivalents", balance_sheet),
                "total_debt": ("Total Debt", balance_sheet),
                "total_assets": ("Total Assets", balance_sheet),
                "total_liabilities": ("Total Liabilities Net Minority Interest", balance_sheet),
                "shareholders_equity": ("Stockholders Equity", balance_sheet),
                "working_capital": (None, None),  # Will calculate
                "capital_expenditure": ("Capital Expenditure", cash_flow),
                "depreciation_and_amortization": ("Depreciation And Amortization", cash_flow),
                "research_and_development": ("Research And Development", income_stmt),
                "goodwill_and_intangible_assets": (None, None),  # Will calculate
                "outstanding_shares": (None, None),  # Will get from info
                "dividends_and_other_cash_distributions": ("Dividends Paid", cash_flow),
                "earnings_per_share": (None, None),  # Will calculate from Net Income / Outstanding Shares
                "book_value_per_share": (None, None),  # Will calculate from Shareholders Equity / Outstanding Shares
                "current_assets": ("Current Assets", balance_sheet),
                "current_liabilities": ("Current Liabilities", balance_sheet),
            }
            
            # Fill in values for each requested line item
            for item in line_items:
                if item in line_item_mapping:
                    field_name, source_df = line_item_mapping[item]
                    
                    # Direct mapping to a field
                    if field_name and source_df is not None:
                        line_item_data[item] = get_value_from_df(source_df, field_name, date)
                    
                    # Special calculations
                    elif item == "gross_margin":
                        gross_profit = get_value_from_df(income_stmt, "Gross Profit", date)
                        revenue = get_value_from_df(income_stmt, "Total Revenue", date)
                        if gross_profit and revenue:
                            line_item_data[item] = gross_profit / revenue
                    
                    elif item == "operating_margin":
                        op_income = get_value_from_df(income_stmt, "Operating Income", date)
                        revenue = get_value_from_df(income_stmt, "Total Revenue", date)
                        if op_income and revenue:
                            line_item_data[item] = op_income / revenue
                    
                    elif item == "free_cash_flow":
                        ocf = get_value_from_df(cash_flow, "Operating Cash Flow", date)
                        capex = get_value_from_df(cash_flow, "Capital Expenditure", date)
                        if ocf and capex:
                            line_item_data[item] = ocf + capex  # CapEx is usually negative
                    
                    elif item == "working_capital":
                        current_assets = get_value_from_df(balance_sheet, "Current Assets", date)
                        current_liabilities = get_value_from_df(balance_sheet, "Current Liabilities", date)
                        if current_assets and current_liabilities:
                            line_item_data[item] = current_assets - current_liabilities
                    
                    elif item == "goodwill_and_intangible_assets":
                        goodwill = get_value_from_df(balance_sheet, "Goodwill", date)
                        intangibles = get_value_from_df(balance_sheet, "Intangible Assets", date)
                        if goodwill or intangibles:
                            line_item_data[item] = (goodwill or 0) + (intangibles or 0)
                    
                    elif item == "outstanding_shares":
                        line_item_data[item] = info.get("sharesOutstanding")
                    
                    elif item == "return_on_invested_capital":
                        net_income = get_value_from_df(income_stmt, "Net Income", date)
                        total_equity = get_value_from_df(balance_sheet, "Stockholders Equity", date)
                        total_debt = get_value_from_df(balance_sheet, "Total Debt", date)
                        if net_income and (total_equity or total_debt):
                            invested_capital = (total_equity or 0) + (total_debt or 0)
                            if invested_capital > 0:
                                line_item_data[item] = net_income / invested_capital
                    
                    elif item == "debt_to_equity":
                        total_debt = get_value_from_df(balance_sheet, "Total Debt", date)
                        total_equity = get_value_from_df(balance_sheet, "Stockholders Equity", date)
                        if total_debt and total_equity and total_equity > 0:
                            line_item_data[item] = total_debt / total_equity
                    
                    elif item == "earnings_per_share":
                        net_income = get_value_from_df(income_stmt, "Net Income", date)
                        shares_outstanding = info.get("sharesOutstanding")
                        if net_income and shares_outstanding and shares_outstanding > 0:
                            line_item_data[item] = net_income / shares_outstanding
                    
                    elif item == "book_value_per_share":
                        shareholders_equity = get_value_from_df(balance_sheet, "Stockholders Equity", date)
                        shares_outstanding = info.get("sharesOutstanding")
                        if shareholders_equity and shares_outstanding and shares_outstanding > 0:
                            line_item_data[item] = shareholders_equity / shares_outstanding
            
            # Create the LineItem object only if we have valid financial data
            # Filter out entries where total_assets is None to prevent analysis issues
            if "total_assets" not in line_items or line_item_data.get("total_assets") is not None:
                result_items.append(LineItem(**line_item_data))
        
        return result_items
        
    except Exception as e:
        print(f"Error fetching line items for {ticker}: {str(e)}")
        return []



def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
) -> list[InsiderTrade]:
    """Fetch insider trades from SEC API or Alpha Vantage."""
    # Check cache first
    if cached_data := _cache.get_insider_trades(ticker):
        # Filter cached data by date range
        filtered_data = [InsiderTrade(**trade) for trade in cached_data 
                        if (start_date is None or (trade.get("transaction_date") or trade["filing_date"]) >= start_date)
                        and (trade.get("transaction_date") or trade["filing_date"]) <= end_date]
        filtered_data.sort(key=lambda x: x.transaction_date or x.filing_date, reverse=True)
        if filtered_data:
            return filtered_data

    # If not in cache or insufficient data, fetch from a free API
    # Using Alpha Vantage (need to get a free API key)
    try:
        alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        
        if not alpha_vantage_key:
            print("No Alpha Vantage API key found. Set ALPHA_VANTAGE_API_KEY in your environment.")
            return []
        
        url = f"https://www.alphavantage.co/query?function=INSIDER_TRANSACTIONS&symbol={ticker}&apikey={alpha_vantage_key}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Error fetching insider data from Alpha Vantage: {response.status_code}")
            return []
            
        data = response.json()
        
        # Extract insider trades
        insider_trades = []
        if 'transactions' in data:
            for trade in data['transactions']:
                filing_date = trade.get('filingDate', '')
                transaction_date = trade.get('transactionDate', '')
                
                # Apply date filtering
                if start_date and transaction_date < start_date:
                    continue
                if end_date and transaction_date > end_date:
                    continue
                
                # Parse values
                try:
                    shares_str = trade.get('numberOfShares', '0').replace(',', '')
                    shares = float(shares_str) if shares_str else 0
                    
                    price_str = trade.get('transactionPrice', '0').replace('$', '').replace(',', '')
                    price = float(price_str) if price_str else 0
                    
                    transaction_value = shares * price
                except (ValueError, TypeError):
                    shares = 0
                    price = 0
                    transaction_value = 0
                
                # Determine if it's a buy or sell
                transaction_type = 'Buy' if 'P - Purchase' in trade.get('transactionType', '') else 'Sale'
                
                insider_trade = InsiderTrade(
                    ticker=ticker,
                    issuer=data.get('symbol', ticker),
                    name=trade.get('reportingName', ''),
                    title=trade.get('reportingPerson', {}).get('title', ''),
                    is_board_director='Director' in trade.get('reportingPerson', {}).get('title', ''),
                    transaction_date=transaction_date,
                    transaction_shares=shares * (1 if transaction_type == 'Buy' else -1),
                    transaction_price_per_share=price,
                    transaction_value=transaction_value,
                    shares_owned_before_transaction=None,  # Not always available
                    shares_owned_after_transaction=None,   # Not always available
                    security_title=trade.get('securityTitle', ''),
                    filing_date=filing_date
                )
                
                insider_trades.append(insider_trade)
        
        # Sort by transaction date, newest first
        insider_trades.sort(key=lambda x: x.transaction_date or '', reverse=True)
        
        # Limit results
        insider_trades = insider_trades[:limit]
        
        # Cache the results
        if insider_trades:
            _cache.set_insider_trades(ticker, [trade.model_dump() for trade in insider_trades])
            
        return insider_trades
        
    except Exception as e:
        print(f"Error fetching insider trades for {ticker}: {str(e)}")
        
        # Fallback to empty result
        return []

def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 100
) -> list[CompanyNews]:
    """Fetch news articles for a ticker."""

    if cached_data := _cache.get_company_news(ticker):
        # Filter cached data by date range
        filtered_data = [CompanyNews(**news) for news in cached_data 
                        if (start_date is None or news["date"] >= start_date)
                        and news["date"] <= end_date]
        filtered_data.sort(key=lambda x: x.date, reverse=True)
        if filtered_data:
            return filtered_data

    # If not in cache or insufficient data, fetch from Yahoo Finance
    try:
        # Convert dates to datetime objects for comparison
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = datetime.strptime(start_date, '%Y-%m-%d') if start_date else end_dt - timedelta(days=90)
        
        # Get news from Yahoo Finance
        def get_yf_news(yf_ticker):
            return yf_ticker.news
        
        news_data = safe_yfinance_request(ticker, get_yf_news)
        
        # Process the news
        news_items = []
        for news in news_data:
            # Get the timestamp and convert to date
            timestamp = news.get('providerPublishTime', 0)
            news_date = datetime.fromtimestamp(timestamp)
            date_str = news_date.strftime('%Y-%m-%d')
            
            # Apply date filtering
            if news_date < start_dt or news_date > end_dt:
                continue
                
            # Extract source and author
            publisher = news.get('publisher', '')
            author = news.get('publisher', '')
            
            # Extract sentiment (not available in Yahoo, set neutral as default)
            sentiment = "neutral"
            
            # Create the news object
            news_item = CompanyNews(
                ticker=ticker,
                title=news.get('title', ''),
                author=author,
                source=publisher,
                date=date_str,
                url=news.get('link', ''),
                sentiment=sentiment
            )
            
            news_items.append(news_item)
            
            # Respect the limit
            if len(news_items) >= limit:
                break
        
        # Sort by date, newest first
        news_items.sort(key=lambda x: x.date, reverse=True)
        
        # Cache the results
        if news_items:
            _cache.set_company_news(ticker, [news.model_dump() for news in news_items])
            
        return news_items
        
    except Exception as e:
        print(f"Error fetching company news for {ticker}: {str(e)}")
        return []


def get_market_cap(
    ticker: str,
    end_date: str,
) -> float | None:
    """Fetch market cap from Yahoo Finance."""
   
        # Try to get from financial metrics as fallback
    financial_metrics = get_financial_metrics(ticker, end_date)
    if financial_metrics and financial_metrics[0].market_cap:
        return financial_metrics[0].market_cap
            
    return None

def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df

def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get price data as a DataFrame."""
    # 调用 get_prices 时不再需要 is_crypto 参数
    # No longer need is_crypto parameter when calling get_prices
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)

# Helper functions
def get_value_from_df(df, field_name, date):
    """Safely extract a value from a dataframe if it exists."""
    if df is None or df.empty or field_name not in df.index:
        return None
        
    try:
        value = df.loc[field_name, date]
        return float(value) if not pd.isna(value) else None
    except (KeyError, ValueError, TypeError):
        return None

def get_comprehensive_data(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    include_line_items: list[str] = None
) -> dict:
    """一次性获取股票的全部数据，避免重复请求
    
    这个函数专门为 agents 设计，一次性获取所有需要的数据：
    - Financial metrics
    - Line items
    - Market cap
    - 原始 yfinance 数据
    
    Args:
        ticker: 股票代码
        end_date: 结束日期
        period: 期间类型
        limit: 数据条数限制
        include_line_items: 需要的特定 line items
        
    Returns:
        包含所有数据的字典
    """
    print(f"🔄 Getting comprehensive data for {ticker}")
    
    try:
        # 使用统一的数据获取器，只请求一次 yfinance
        yf_dataset = get_yfinance_data(ticker)
        
        # 获取 financial metrics
        financial_metrics = get_financial_metrics(ticker, end_date, period, limit)
        
        # 获取 line items (如果指定了)
        line_items = []
        if include_line_items:
            line_items = search_line_items(ticker, include_line_items, end_date, period, limit)
        
        # 获取 market cap
        market_cap = None
        if financial_metrics and financial_metrics[0].market_cap:
            market_cap = financial_metrics[0].market_cap
        
        # 返回综合数据
        result = {
            "ticker": ticker,
            "financial_metrics": financial_metrics,
            "line_items": line_items,
            "market_cap": market_cap,
            "yfinance_dataset": yf_dataset,  # 原始数据，供高级分析使用
            "data_timestamp": yf_dataset.fetch_timestamp,
            "data_age_seconds": time.time() - yf_dataset.fetch_timestamp
        }
        
        print(f"✅ Successfully retrieved comprehensive data for {ticker}")
        return result
        
    except Exception as e:
        print(f"❌ Error getting comprehensive data for {ticker}: {str(e)}")
        return {
            "ticker": ticker,
            "financial_metrics": [],
            "line_items": [],
            "market_cap": None,
            "yfinance_dataset": None,
            "error": str(e)
        }


def get_batch_comprehensive_data(
    tickers: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    common_line_items: list[str] = None
) -> dict[str, dict]:
    """批量获取多个股票的综合数据
    
    这个函数为多股票分析优化，可以显著减少 API 调用次数。
    
    Args:
        tickers: 股票代码列表
        end_date: 结束日期
        period: 期间类型
        limit: 数据条数限制
        common_line_items: 所有股票共同需要的 line items
        
    Returns:
        ticker 到综合数据的映射
    """
    print(f"🚀 Getting batch comprehensive data for {len(tickers)} tickers")
    
    # 首先批量获取所有 yfinance 数据
    yf_datasets = get_batch_yfinance_data(tickers)
    
    results = {}
    
    for ticker in tickers:
        try:
            if ticker in yf_datasets:
                # 数据已经获取，直接处理
                print(f"📊 Processing data for {ticker}")
                result = get_comprehensive_data(ticker, end_date, period, limit, common_line_items)
                results[ticker] = result
            else:
                # 数据获取失败
                print(f"❌ No data available for {ticker}")
                results[ticker] = {
                    "ticker": ticker,
                    "financial_metrics": [],
                    "line_items": [],
                    "market_cap": None,
                    "yfinance_dataset": None,
                    "error": "Failed to fetch yfinance data"
                }
        except Exception as e:
            print(f"❌ Error processing {ticker}: {str(e)}")
            results[ticker] = {
                "ticker": ticker,
                "financial_metrics": [],
                "line_items": [],
                "market_cap": None,
                "yfinance_dataset": None,
                "error": str(e)
            }
    
    print(f"✅ Batch processing completed for {len(results)} tickers")
    return results


