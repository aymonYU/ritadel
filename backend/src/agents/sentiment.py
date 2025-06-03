"""
情绪分析代理 - 市场情绪与内部交易分析系统
Sentiment Analysis Agent - Market sentiment and insider trading analysis system

综合分析内部交易模式和新闻情绪，生成投资信号
Analyzes insider trading patterns and news sentiment to generate investment signals
"""
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import pandas as pd
import numpy as np
import json

from tools.api import get_insider_trades, get_company_news


##### 情绪代理 - Sentiment Agent #####
def sentiment_agent(state: AgentState):
    """
    分析市场情绪并为多个股票代码生成交易信号：
    1. 内部交易模式分析 - 高管买卖行为反映对公司前景的信心
    2. 新闻情绪分析 - 媒体报道的情绪倾向
    3. 加权信号组合 - 结合两种信号源生成综合判断
    4. 置信度计算 - 基于信号强度和一致性
    
    Analyzes market sentiment and generates trading signals for multiple tickers:
    1. Insider trading pattern analysis - Executive buying/selling reflects confidence in company prospects
    2. News sentiment analysis - Emotional tone of media coverage
    3. Weighted signal combination - Combines both signal sources for comprehensive judgment
    4. Confidence calculation - Based on signal strength and consistency
    """
    data = state.get("data", {})
    end_date = data.get("end_date")
    tickers = data.get("tickers")

    # 为每个股票代码初始化情绪分析 - Initialize sentiment analysis for each ticker
    sentiment_analysis = {}

    for ticker in tickers:
        progress.update_status("sentiment_agent", ticker, "Fetching insider trades")

        # 获取内部交易数据 - Get the insider trades
        insider_trades = get_insider_trades(
            ticker=ticker,
            end_date=end_date,
            limit=1000,
        )

        progress.update_status("sentiment_agent", ticker, "Analyzing trading patterns")

        # 从内部交易中获取信号 - Get the signals from the insider trades
        # 负值表示卖出（看跌），正值表示买入（看涨）- Negative values indicate selling (bearish), positive values indicate buying (bullish)
        transaction_shares = pd.Series([t.transaction_shares for t in insider_trades]).dropna()
        insider_signals = np.where(transaction_shares < 0, "bearish", "bullish").tolist()

        progress.update_status("sentiment_agent", ticker, "Fetching company news")

        # 获取公司新闻 - Get the company news
        company_news = get_company_news(ticker, end_date, limit=100)

        # 从公司新闻中获取情绪 - Get the sentiment from the company news
        sentiment = pd.Series([n.sentiment for n in company_news]).dropna()
        news_signals = np.where(sentiment == "negative", "bearish", 
                              np.where(sentiment == "positive", "bullish", "neutral")).tolist()
        
        progress.update_status("sentiment_agent", ticker, "Combining signals")
        # 使用权重组合两个信号源 - Combine signals from both sources with weights
        insider_weight = 0.3  # 内部交易权重30% - Insider trading weight 30%
        news_weight = 0.7     # 新闻情绪权重70% - News sentiment weight 70%
        
        # 计算加权信号计数 - Calculate weighted signal counts
        bullish_signals = (
            insider_signals.count("bullish") * insider_weight +
            news_signals.count("bullish") * news_weight
        )
        bearish_signals = (
            insider_signals.count("bearish") * insider_weight +
            news_signals.count("bearish") * news_weight
        )

        # 确定整体信号 - Determine overall signal
        if bullish_signals > bearish_signals:
            overall_signal = "bullish"
        elif bearish_signals > bullish_signals:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"

        # 基于加权比例计算置信度 - Calculate confidence level based on the weighted proportion
        total_weighted_signals = len(insider_signals) * insider_weight + len(news_signals) * news_weight
        confidence = 0  # 无信号时的默认置信度 - Default confidence when there are no signals
        if total_weighted_signals > 0:
            confidence = round(max(bullish_signals, bearish_signals) / total_weighted_signals, 2) * 100
        reasoning = f"加权看涨信号: {bullish_signals:.1f}, 加权看跌信号: {bearish_signals:.1f} - Weighted Bullish signals: {bullish_signals:.1f}, Weighted Bearish signals: {bearish_signals:.1f}"

        sentiment_analysis[ticker] = {
            "signal": overall_signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status("sentiment_agent", ticker, "Done")

    # 创建情绪消息 - Create the sentiment message
    message = HumanMessage(
        content=json.dumps(sentiment_analysis),
        name="sentiment_agent",
    )

    # 如果设置了标志则打印推理过程 - Print the reasoning if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(sentiment_analysis, "Sentiment Analysis Agent")

    # 将信号添加到analyst_signals列表 - Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["sentiment_agent"] = sentiment_analysis

    return {
        "messages": [message],
        "data": data,
    }
