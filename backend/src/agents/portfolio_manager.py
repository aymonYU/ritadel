"""
投资组合管理代理 - 多资产交易决策系统
Portfolio Management Agent - Multi-asset trading decision system

基于分析师信号做出最终交易决策，支持多头和空头策略
Makes final trading decisions based on analyst signals, supporting both long and short strategies
"""
import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm


class PortfolioDecision(BaseModel):
    """投资组合交易决策模型 - Portfolio trading decision model"""
    action: Literal["buy", "sell", "short", "cover", "hold"] = Field(description="交易动作：买入/卖出/做空/平仓/持有 - Trading action: buy/sell/short/cover/hold")
    quantity: int = Field(description="交易股数 - Number of shares to trade")
    confidence: float = Field(description="决策置信度，0.0到100.0之间 - Confidence in the decision, between 0.0 and 100.0")
    reasoning: str = Field(description="决策推理 - Reasoning for the decision")


class PortfolioManagerOutput(BaseModel):
    """投资组合管理输出模型 - Portfolio management output model"""
    decisions: dict[str, PortfolioDecision] = Field(description="股票代码到交易决策的字典 - Dictionary of ticker to trading decisions")


##### 投资组合管理代理 - Portfolio Management Agent #####
def portfolio_management_agent(state: AgentState):
    """
    为多个股票代码做出最终交易决策并生成订单：
    1. 分析分析师信号 - 综合各分析师的买卖建议
    2. 考虑风险限制 - 遵守仓位限制和资金管理
    3. 支持多空策略 - 可以做多头或空头操作
    4. 生成具体订单 - 确定交易数量和动作
    
    Makes final trading decisions and generates orders for multiple tickers:
    1. Analyze analyst signals - Synthesize recommendations from all analysts
    2. Consider risk constraints - Respect position limits and money management
    3. Support long/short strategies - Can execute both long and short positions
    4. Generate specific orders - Determine trading quantity and action
    """

    # 获取投资组合和分析师信号 - Get the portfolio and analyst signals
    portfolio = state["data"]["portfolio"]
    analyst_signals = state["data"]["analyst_signals"]
    tickers = state["data"]["tickers"]

    progress.update_status("portfolio_management_agent", None, "Analyzing signals")

    # 为每个股票代码获取仓位限制、当前价格和信号 - Get position limits, current prices, and signals for every ticker
    position_limits = {}      # 仓位限制 - Position limits
    current_prices = {}       # 当前价格 - Current prices
    max_shares = {}          # 最大股数 - Maximum shares
    signals_by_ticker = {}   # 按股票分组的信号 - Signals grouped by ticker
    
    for ticker in tickers:
        progress.update_status("portfolio_management_agent", ticker, "Processing analyst signals")

        # 获取该股票的仓位限制和当前价格 - Get position limits and current prices for the ticker
        risk_data = analyst_signals.get("risk_management_agent", {}).get(ticker, {})
        position_limits[ticker] = risk_data.get("remaining_position_limit", 0)
        current_prices[ticker] = risk_data.get("current_price", 0)

        # 基于仓位限制和价格计算最大允许股数 - Calculate maximum shares allowed based on position limit and price
        if current_prices[ticker] > 0:
            max_shares[ticker] = int(position_limits[ticker] / current_prices[ticker])
        else:
            max_shares[ticker] = 0

        # 获取该股票的信号 - Get signals for the ticker
        ticker_signals = {}
        for agent, signals in analyst_signals.items():
            if agent != "risk_management_agent" and ticker in signals:
                ticker_signals[agent] = {"signal": signals[ticker]["signal"], "confidence": signals[ticker]["confidence"]}
        signals_by_ticker[ticker] = ticker_signals

    progress.update_status("portfolio_management_agent", None, "Making trading decisions")

    # 生成交易决策 - Generate the trading decision
    result = generate_trading_decision(
        tickers=tickers,
        signals_by_ticker=signals_by_ticker,
        current_prices=current_prices,
        max_shares=max_shares,
        portfolio=portfolio,
    )

    # 将Pydantic模型转换为字典后存储 - Convert Pydantic models to dictionaries before storing
    decisions_dict = {ticker: decision.model_dump() for ticker, decision in result.decisions.items()}
    
    # 将决策作为字典存储在状态数据中 - Store the decisions in the state data as dictionaries
    state["data"]["portfolio_decision"] = decisions_dict

    # 创建投资组合管理消息 - Create the portfolio management message
    message = HumanMessage(
        content=json.dumps(decisions_dict),
        name="portfolio_management_agent",
    )

    # 如果设置了标志则打印决策 - Print the decision if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(decisions_dict, "Portfolio Management Agent")

    progress.update_status("portfolio_management_agent", None, "Done")

    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
    }


def generate_trading_decision(
    tickers: list[str],
    signals_by_ticker: dict[str, dict],
    current_prices: dict[str, float],
    max_shares: dict[str, int],
    portfolio: dict[str, float],
) -> PortfolioManagerOutput:
    """
    使用重试逻辑尝试从LLM获取决策
    基于多种分析师信号生成具体的交易指令
    
    Attempts to get a decision from the LLM with retry logic
    Generates specific trading instructions based on multiple analyst signals
    """
    # 创建提示模板 - Create the prompt template
    template = ChatPromptTemplate.from_messages(
        [
            (
              "system",
              """你是一位投资组合经理，基于多个股票代码做出最终交易决策。

              交易规则：
              - 多头仓位：
                * 只有在有可用现金时才能买入
                * 只有在当前持有该股票多头股份时才能卖出
                * 卖出数量必须≤当前多头仓位股数
                * 买入数量必须≤该股票的max_shares
              
              - 空头仓位：
                * 只有在有可用保证金时才能做空（需要仓位价值的50%作为保证金）
                * 只有在当前持有该股票空头股份时才能平仓
                * 平仓数量必须≤当前空头仓位股数
                * 做空数量必须符合保证金要求
              
              - max_shares值已预先计算以遵守仓位限制
              - 基于信号考虑多头和空头机会
              - 通过多头和空头敞口维持适当的风险管理

              可用动作：
              - "buy": 开仓或增加多头仓位
              - "sell": 平仓或减少多头仓位
              - "short": 开仓或增加空头仓位
              - "cover": 平仓或减少空头仓位
              - "hold": 无动作

              输入参数：
              - signals_by_ticker: 股票代码→信号的字典
              - max_shares: 每个股票允许的最大股数
              - portfolio_cash: 投资组合中的当前现金
              - portfolio_positions: 当前仓位（多头和空头）
              - current_prices: 每个股票的当前价格
              - margin_requirement: 空头仓位的当前保证金要求
              
              You are a portfolio manager making final trading decisions based on multiple tickers.

              Trading Rules:
              - For long positions:
                * Only buy if you have available cash
                * Only sell if you currently hold long shares of that ticker
                * Sell quantity must be ≤ current long position shares
                * Buy quantity must be ≤ max_shares for that ticker
              
              - For short positions:
                * Only short if you have available margin (50% of position value required)
                * Only cover if you currently have short shares of that ticker
                * Cover quantity must be ≤ current short position shares
                * Short quantity must respect margin requirements
              
              - The max_shares values are pre-calculated to respect position limits
              - Consider both long and short opportunities based on signals
              - Maintain appropriate risk management with both long and short exposure

              Available Actions:
              - "buy": Open or add to long position
              - "sell": Close or reduce long position
              - "short": Open or add to short position
              - "cover": Close or reduce short position
              - "hold": No action

              Inputs:
              - signals_by_ticker: dictionary of ticker → signals
              - max_shares: maximum shares allowed per ticker
              - portfolio_cash: current cash in portfolio
              - portfolio_positions: current positions (both long and short)
              - current_prices: current prices for each ticker
              - margin_requirement: current margin requirement for short positions
              """,
            ),
            (
              "human",
              """基于团队分析，为每个股票代码做出交易决策。

              按股票分组的信号：
              {signals_by_ticker}

              当前价格：
              {current_prices}

              购买允许的最大股数：
              {max_shares}

              投资组合现金：{portfolio_cash}
              当前仓位：{portfolio_positions}
              当前保证金要求：{margin_requirement}

              严格按以下JSON结构输出：
              {{
                "decisions": {{
                  "TICKER1": {{
                    "action": "buy/sell/short/cover/hold",
                    "quantity": integer,
                    "confidence": float,
                    "reasoning": "string"
                  }},
                  "TICKER2": {{
                    ...
                  }},
                  ...
                }}
              }}
              
              Based on the team's analysis, make your trading decisions for each ticker.

              Here are the signals by ticker:
              {signals_by_ticker}

              Current Prices:
              {current_prices}

              Maximum Shares Allowed For Purchases:
              {max_shares}

              Portfolio Cash: {portfolio_cash}
              Current Positions: {portfolio_positions}
              Current Margin Requirement: {margin_requirement}

              Output strictly in JSON with the following structure:
              {{
                "decisions": {{
                  "TICKER1": {{
                    "action": "buy/sell/short/cover/hold",
                    "quantity": integer,
                    "confidence": float,
                    "reasoning": "string"
                  }},
                  "TICKER2": {{
                    ...
                  }},
                  ...
                }}
              }}
              """,
            ),
        ]
    )

    # 生成提示 - Generate the prompt
    prompt = template.invoke(
        {
            "signals_by_ticker": json.dumps(signals_by_ticker, indent=2),
            "current_prices": json.dumps(current_prices, indent=2),
            "max_shares": json.dumps(max_shares, indent=2),
            "portfolio_cash": f"{portfolio.get('cash', 0):.2f}",
            "portfolio_positions": json.dumps(portfolio.get('positions', {}), indent=2),
            "margin_requirement": f"{portfolio.get('margin_requirement', 0):.2f}",
        }
    )

    # 为PortfolioManagerOutput创建默认工厂 - Create default factory for PortfolioManagerOutput
    def create_default_portfolio_output():
        return PortfolioManagerOutput(decisions={ticker: PortfolioDecision(action="hold", quantity=0, confidence=0.0, reasoning="投资组合管理出错，默认持有 - Error in portfolio management, defaulting to hold") for ticker in tickers})

    # 调用LLM时不再传递model_name和model_provider - model_name and model_provider are no longer passed when calling call_llm
    return call_llm(prompt=prompt, pydantic_model=PortfolioManagerOutput, agent_name="portfolio_management_agent", default_factory=create_default_portfolio_output)
