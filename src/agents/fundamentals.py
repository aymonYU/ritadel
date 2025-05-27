"""
基本面分析代理 - 财务数据基本面分析系统
Fundamental Analysis Agent - Financial data fundamental analysis system

分析公司财务指标，评估盈利能力、增长性、财务健康度和估值水平
Analyzes company financial metrics, evaluating profitability, growth, financial health and valuation levels
"""
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json

from tools.api import get_financial_metrics


##### 基本面代理 - Fundamental Agent #####
def fundamentals_agent(state: AgentState):
    """
    分析基本面数据并为多个股票代码生成交易信号：
    1. 盈利能力分析 - ROE、净利润率、营业利润率
    2. 成长性分析 - 收入增长、盈利增长、账面价值增长
    3. 财务健康度 - 流动比率、负债权益比、自由现金流
    4. 估值比率分析 - P/E、P/B、P/S等估值指标
    
    Analyzes fundamental data and generates trading signals for multiple tickers:
    1. Profitability analysis - ROE, net margin, operating margin
    2. Growth analysis - Revenue growth, earnings growth, book value growth
    3. Financial health - Current ratio, debt-to-equity, free cash flow
    4. Valuation ratios - P/E, P/B, P/S and other valuation metrics
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    # 为每个股票代码初始化基本面分析 - Initialize fundamental analysis for each ticker
    fundamental_analysis = {}

    for ticker in tickers:
        progress.update_status("fundamentals_agent", ticker, "Fetching financial metrics")

        # 获取财务指标 - Get the financial metrics
        financial_metrics = get_financial_metrics(
            ticker=ticker,
            end_date=end_date,
            period="ttm",  # TTM - 过去十二个月 - TTM - Trailing Twelve Months
            limit=10,
        )

        if not financial_metrics:
            progress.update_status("fundamentals_agent", ticker, "Failed: No financial metrics found")
            continue

        # 获取最新的财务指标 - Pull the most recent financial metrics
        metrics = financial_metrics[0]

        # 为不同基本面方面初始化信号列表 - Initialize signals list for different fundamental aspects
        signals = []
        reasoning = {}

        progress.update_status("fundamentals_agent", ticker, "Analyzing profitability")
        # 1. 盈利能力分析 - Profitability Analysis
        return_on_equity = metrics.return_on_equity      # 净资产收益率 - Return on Equity
        net_margin = metrics.net_margin                  # 净利润率 - Net Profit Margin
        operating_margin = metrics.operating_margin      # 营业利润率 - Operating Margin

        # 盈利能力阈值标准 - Profitability threshold criteria
        thresholds = [
            (return_on_equity, 0.15),    # 强劲的ROE大于15% - Strong ROE above 15%
            (net_margin, 0.20),          # 健康的净利润率大于20% - Healthy profit margins above 20%
            (operating_margin, 0.15),    # 强劲的营业效率大于15% - Strong operating efficiency above 15%
        ]
        profitability_score = sum(metric is not None and metric > threshold for metric, threshold in thresholds)

        signals.append("bullish" if profitability_score >= 2 else "bearish" if profitability_score == 0 else "neutral")
        reasoning["profitability_signal"] = {
            "signal": signals[0],
            "details": (f"ROE: {return_on_equity:.2%}" if return_on_equity else "ROE: N/A") + ", " + (f"净利润率: {net_margin:.2%}" if net_margin else "净利润率: N/A") + ", " + (f"营业利润率: {operating_margin:.2%}" if operating_margin else "营业利润率: N/A"),
        }

        progress.update_status("fundamentals_agent", ticker, "Analyzing growth")
        # 2. 成长性分析 - Growth Analysis
        revenue_growth = metrics.revenue_growth        # 收入增长率 - Revenue Growth
        earnings_growth = metrics.earnings_growth      # 盈利增长率 - Earnings Growth
        book_value_growth = metrics.book_value_growth  # 账面价值增长率 - Book Value Growth

        # 成长性阈值标准 - Growth threshold criteria
        thresholds = [
            (revenue_growth, 0.10),     # 10%收入增长 - 10% revenue growth
            (earnings_growth, 0.10),    # 10%盈利增长 - 10% earnings growth
            (book_value_growth, 0.10),  # 10%账面价值增长 - 10% book value growth
        ]
        growth_score = sum(metric is not None and metric > threshold for metric, threshold in thresholds)

        signals.append("bullish" if growth_score >= 2 else "bearish" if growth_score == 0 else "neutral")
        reasoning["growth_signal"] = {
            "signal": signals[1],
            "details": (f"收入增长: {revenue_growth:.2%}" if revenue_growth else "收入增长: N/A") + ", " + (f"盈利增长: {earnings_growth:.2%}" if earnings_growth else "盈利增长: N/A"),
        }

        progress.update_status("fundamentals_agent", ticker, "Analyzing financial health")
        # 3. 财务健康度分析 - Financial Health Analysis
        current_ratio = metrics.current_ratio                          # 流动比率 - Current Ratio
        debt_to_equity = metrics.debt_to_equity                        # 负债权益比 - Debt-to-Equity Ratio
        free_cash_flow_per_share = metrics.free_cash_flow_per_share    # 每股自由现金流 - Free Cash Flow per Share
        earnings_per_share = metrics.earnings_per_share                # 每股收益 - Earnings per Share

        health_score = 0
        if current_ratio and current_ratio > 1.5:  # 强劲的流动性 - Strong liquidity
            health_score += 1
        if debt_to_equity and debt_to_equity < 0.5:  # 保守的债务水平 - Conservative debt levels
            health_score += 1
        if free_cash_flow_per_share and earnings_per_share and free_cash_flow_per_share > earnings_per_share * 0.8:  # 强劲的自由现金流转换 - Strong FCF conversion
            health_score += 1

        signals.append("bullish" if health_score >= 2 else "bearish" if health_score == 0 else "neutral")
        reasoning["financial_health_signal"] = {
            "signal": signals[2],
            "details": (f"流动比率: {current_ratio:.2f}" if current_ratio else "流动比率: N/A") + ", " + (f"负债权益比: {debt_to_equity:.2f}" if debt_to_equity else "负债权益比: N/A"),
        }

        progress.update_status("fundamentals_agent", ticker, "Analyzing valuation ratios")
        # 4. 估值比率分析 - Price-to-X Ratios Analysis
        pe_ratio = metrics.price_to_earnings_ratio  # 市盈率 - Price-to-Earnings Ratio
        pb_ratio = metrics.price_to_book_ratio      # 市净率 - Price-to-Book Ratio
        ps_ratio = metrics.price_to_sales_ratio     # 市销率 - Price-to-Sales Ratio

        # 估值比率阈值（值越高表示越贵）- Valuation ratio thresholds (higher values indicate more expensive)
        thresholds = [
            (pe_ratio, 25),  # 合理的市盈率小于25 - Reasonable P/E ratio below 25
            (pb_ratio, 3),   # 合理的市净率小于3 - Reasonable P/B ratio below 3
            (ps_ratio, 5),   # 合理的市销率小于5 - Reasonable P/S ratio below 5
        ]
        # 注意：这里计算的是"过高"的估值比率数量 - Note: This counts "excessive" valuation ratios
        price_ratio_score = sum(metric is not None and metric > threshold for metric, threshold in thresholds)

        # 估值比率越高越看跌（价格过高）- Higher valuation ratios are more bearish (overpriced)
        signals.append("bearish" if price_ratio_score >= 2 else "bullish" if price_ratio_score == 0 else "neutral")
        reasoning["price_ratios_signal"] = {
            "signal": signals[3],
            "details": (f"市盈率: {pe_ratio:.2f}" if pe_ratio else "市盈率: N/A") + ", " + (f"市净率: {pb_ratio:.2f}" if pb_ratio else "市净率: N/A") + ", " + (f"市销率: {ps_ratio:.2f}" if ps_ratio else "市销率: N/A"),
        }

        progress.update_status("fundamentals_agent", ticker, "Calculating final signal")
        # 确定整体信号 - Determine overall signal
        bullish_signals = signals.count("bullish")
        bearish_signals = signals.count("bearish")

        if bullish_signals > bearish_signals:
            overall_signal = "bullish"
        elif bearish_signals > bullish_signals:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"

        # 计算置信度 - Calculate confidence level
        total_signals = len(signals)
        confidence = round(max(bullish_signals, bearish_signals) / total_signals, 2) * 100

        fundamental_analysis[ticker] = {
            "signal": overall_signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status("fundamentals_agent", ticker, "Done")

    # 创建基本面分析消息 - Create the fundamental analysis message
    message = HumanMessage(
        content=json.dumps(fundamental_analysis),
        name="fundamentals_agent",
    )

    # 如果设置了标志则打印推理过程 - Print the reasoning if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(fundamental_analysis, "Fundamental Analysis Agent")

    # 将信号添加到analyst_signals列表 - Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["fundamentals_agent"] = fundamental_analysis

    return {
        "messages": [message],
        "data": data,
    }
