"""
风险管理代理 - 基于实际风险因素的头寸控制系统
Risk Management Agent - Position control system based on real-world risk factors

控制基于投资组合风险的头寸规模，确保资金管理和风险分散
Controls position sizing based on portfolio risk, ensuring proper money management and risk diversification
"""
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
from tools.api import get_prices, prices_to_df
import json


##### 风险管理代理 - Risk Management Agent #####
def risk_management_agent(state: AgentState):
    """
    基于实际风险因素控制多个股票代码的头寸规模：
    1. 单一股票头寸限制 - 投资组合价值的20%
    2. 现金可用性管理 - 确保有足够资金
    3. 风险分散原则 - 避免过度集中投资
    4. 动态头寸调整 - 基于当前持仓和价格变化
    
    Controls position sizing based on real-world risk factors for multiple tickers:
    1. Single stock position limit - 20% of portfolio value
    2. Cash availability management - Ensure sufficient funds
    3. Risk diversification principle - Avoid over-concentration
    4. Dynamic position adjustment - Based on current holdings and price changes
    """
    portfolio = state["data"]["portfolio"]
    data = state["data"]
    tickers = data["tickers"]

    # 为每个股票代码初始化风险分析 - Initialize risk analysis for each ticker
    risk_analysis = {}
    current_prices = {}  # 存储价格以避免冗余API调用 - Store prices to avoid redundant API calls

    for ticker in tickers:
        progress.update_status("risk_management_agent", ticker, "Analyzing price data")

        # 获取价格数据 - Get price data
        prices = get_prices(
            ticker=ticker,
            start_date=data["start_date"],
            end_date=data["end_date"],
        )

        if not prices:
            progress.update_status("risk_management_agent", ticker, "Failed: No price data found")
            continue

        prices_df = prices_to_df(prices)

        progress.update_status("risk_management_agent", ticker, "Calculating position limits")

        # 计算投资组合价值 - Calculate portfolio value
        current_price = prices_df["close"].iloc[-1]  # 获取最新收盘价 - Get latest closing price
        current_prices[ticker] = current_price  # 存储当前价格 - Store the current price

        # 计算此股票的当前头寸价值 - Calculate current position value for this ticker
        current_position_value = portfolio.get("cost_basis", {}).get(ticker, 0)

        # 使用存储的价格计算总投资组合价值 - Calculate total portfolio value using stored prices
        total_portfolio_value = portfolio.get("cash", 0) + sum(portfolio.get("cost_basis", {}).get(t, 0) for t in portfolio.get("cost_basis", {}))

        # 基础限制：任意单一头寸占投资组合的20% - Base limit is 20% of portfolio for any single position
        position_limit = total_portfolio_value * 0.20

        # 对于现有头寸，从限制中减去当前头寸价值 - For existing positions, subtract current position value from limit
        remaining_position_limit = position_limit - current_position_value

        # 确保不超过可用现金 - Ensure we don't exceed available cash
        max_position_size = min(remaining_position_limit, portfolio.get("cash", 0))

        risk_analysis[ticker] = {
            "remaining_position_limit": float(max_position_size),  # 剩余可投资金额 - Remaining investable amount
            "current_price": float(current_price),                 # 当前股价 - Current stock price
            "reasoning": {
                "portfolio_value": float(total_portfolio_value),     # 投资组合总值 - Total portfolio value
                "current_position": float(current_position_value),   # 当前持仓价值 - Current position value
                "position_limit": float(position_limit),            # 头寸限制 - Position limit
                "remaining_limit": float(remaining_position_limit), # 剩余限制 - Remaining limit
                "available_cash": float(portfolio.get("cash", 0)),  # 可用现金 - Available cash
            },
        }

        progress.update_status("risk_management_agent", ticker, "Done")

    # 创建风险管理消息 - Create risk management message
    message = HumanMessage(
        content=json.dumps(risk_analysis),
        name="risk_management_agent",
    )

    # 如果设置了标志则打印推理过程 - Print reasoning if flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(risk_analysis, "Risk Management Agent")

    # 将信号添加到analyst_signals列表 - Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["risk_management_agent"] = risk_analysis

    return {
        "messages": state["messages"] + [message],
        "data": data,
    }
