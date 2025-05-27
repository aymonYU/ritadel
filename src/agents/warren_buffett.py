"""
Warren Buffett价值投资分析师代理 - 基于沃伦·巴菲特的投资原则
Warren Buffett value investing analyst agent - Based on Warren Buffett's investment principles
"""
from graph.state import AgentState, show_agent_reasoning
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from tools.api import get_financial_metrics, get_market_cap, search_line_items
from utils.llm import call_llm
from utils.progress import progress


class WarrenBuffettSignal(BaseModel):
    """
    Warren Buffett分析信号模型 - 包含投资信号、置信度和推理
    Warren Buffett analysis signal model - Contains investment signal, confidence and reasoning
    """
    signal: Literal["买入", "卖出", "中性"]
    confidence: float
    reasoning: str


def warren_buffett_agent(state: AgentState):
    """
    使用巴菲特的投资原则分析股票，包括LLM推理
    运用巴菲特的核心投资理念：
    1. 寻找具有可持续竞争优势的高质量企业
    2. 强调长期增长和盈利稳定性
    3. 注重内在价值与市场价格的安全边际
    4. 偏好简单易懂的商业模式
    
    Analyzes stocks using Buffett's principles and LLM reasoning.
    Applies Buffett's core investment philosophy:
    1. Look for high-quality companies with sustainable competitive advantages
    2. Emphasize long-term growth and earnings stability  
    3. Focus on margin of safety between intrinsic value and market price
    4. Prefer simple, understandable business models
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    # 收集所有分析数据供LLM推理 - Collect all analysis for LLM reasoning
    analysis_data = {}
    buffett_analysis = {}

    for ticker in tickers:
        progress.update_status("warren_buffett_agent", ticker, "Fetching financial metrics")
        # 获取所需数据 - Fetch required data
        metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=5)

        progress.update_status("warren_buffett_agent", ticker, "Gathering financial line items")
        financial_line_items = search_line_items(
            ticker,
            [
                "capital_expenditure",
                "depreciation_and_amortization",
                "net_income",
                "outstanding_shares",
                "total_assets",
                "total_liabilities",
            ],
            end_date,
            period="ttm",
            limit=5,
        )

        progress.update_status("warren_buffett_agent", ticker, "Getting market cap")
        # 获取当前市值 - Get current market cap
        market_cap = get_market_cap(ticker, end_date)

        progress.update_status("warren_buffett_agent", ticker, "Analyzing fundamentals")
        # 分析基本面 - Analyze fundamentals
        fundamental_analysis = analyze_fundamentals(metrics)

        progress.update_status("warren_buffett_agent", ticker, "Analyzing consistency")
        consistency_analysis = analyze_consistency(financial_line_items)

        progress.update_status("warren_buffett_agent", ticker, "Calculating intrinsic value")
        intrinsic_value_analysis = calculate_intrinsic_value(financial_line_items)

        # 计算总分 - Calculate total score
        total_score = fundamental_analysis["score"] + consistency_analysis["score"]
        max_possible_score = 10

        # 如果有内在价值和当前价格，添加安全边际分析
        # Add margin of safety analysis if we have both intrinsic value and current price
        margin_of_safety = None
        intrinsic_value = intrinsic_value_analysis["intrinsic_value"]
        if intrinsic_value and market_cap:
            margin_of_safety = (intrinsic_value - market_cap) / market_cap

            # 如果有良好的安全边际（>30%），加分
            # Add to score if there's a good margin of safety (>30%)
            if margin_of_safety > 0.3:
                total_score += 2
                max_possible_score += 2

        # 生成交易信号 - Generate trading signal
        if total_score >= 0.7 * max_possible_score:
            signal = "买入"
        elif total_score <= 0.3 * max_possible_score:
            signal = "卖出"
        else:
            signal = "中性"

        # 合并所有分析结果 - Combine all analysis results
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "fundamental_analysis": fundamental_analysis,
            "consistency_analysis": consistency_analysis,
            "intrinsic_value_analysis": intrinsic_value_analysis,
            "market_cap": market_cap,
            "margin_of_safety": margin_of_safety,
        }

        progress.update_status("warren_buffett_agent", ticker, "Generating Buffett analysis")
        buffett_output = generate_buffett_output(
            ticker=ticker,
            analysis_data=analysis_data,
        )

        # 以与其他代理一致的格式存储分析
        # Store analysis in consistent format with other agents
        buffett_analysis[ticker] = {
            "signal": buffett_output.signal,
            "confidence": buffett_output.confidence,
            "reasoning": buffett_output.reasoning,
        }

        progress.update_status("warren_buffett_agent", ticker, "Done")

    # 创建消息 - Create the message
    message = HumanMessage(content=json.dumps(buffett_analysis), name="warren_buffett_agent")

    # 如果请求，显示推理过程 - Show reasoning if requested
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(buffett_analysis, "Warren Buffett Agent")

    # 将信号添加到分析师信号列表 - Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["warren_buffett_agent"] = buffett_analysis

    return {"messages": [message], "data": state["data"]}


def analyze_fundamentals(metrics: list) -> dict[str, any]:
    """
    基于巴菲特标准分析公司基本面
    关注指标：ROE、债务股权比、营业利润率、流动比率
    
    Analyze company fundamentals based on Buffett's criteria.
    Focus metrics: ROE, debt-to-equity, operating margin, current ratio
    """
    if not metrics:
        return {"score": 0, "details": "Insufficient fundamental data"}

    # 获取最新指标 - Get latest metrics
    latest_metrics = metrics[0]

    score = 0
    reasoning = []

    # 检查ROE（股本回报率）- Check ROE (Return on Equity)
    if latest_metrics.return_on_equity and latest_metrics.return_on_equity > 0.15:  # 15% ROE threshold
        score += 2
        reasoning.append(f"Strong ROE of {latest_metrics.return_on_equity:.1%}")
    elif latest_metrics.return_on_equity:
        reasoning.append(f"Weak ROE of {latest_metrics.return_on_equity:.1%}")
    else:
        reasoning.append("ROE data not available")

    # 检查债务股权比 - Check Debt to Equity
    if latest_metrics.debt_to_equity and latest_metrics.debt_to_equity < 0.5:
        score += 2
        reasoning.append("Conservative debt levels")
    elif latest_metrics.debt_to_equity:
        reasoning.append(f"High debt to equity ratio of {latest_metrics.debt_to_equity:.1f}")
    else:
        reasoning.append("Debt to equity data not available")

    # 检查营业利润率 - Check Operating Margin
    if latest_metrics.operating_margin and latest_metrics.operating_margin > 0.15:
        score += 2
        reasoning.append("Strong operating margins")
    elif latest_metrics.operating_margin:
        reasoning.append(f"Weak operating margin of {latest_metrics.operating_margin:.1%}")
    else:
        reasoning.append("Operating margin data not available")

    # 检查流动比率 - Check Current Ratio
    if latest_metrics.current_ratio and latest_metrics.current_ratio > 1.5:
        score += 1
        reasoning.append("Good liquidity position")
    elif latest_metrics.current_ratio:
        reasoning.append(f"Weak liquidity with current ratio of {latest_metrics.current_ratio:.1f}")
    else:
        reasoning.append("Current ratio data not available")

    return {"score": score, "details": "; ".join(reasoning), "metrics": latest_metrics.model_dump()}


def analyze_consistency(financial_line_items: list) -> dict[str, any]:
    """
    分析盈利一致性和增长性
    巴菲特偏好长期稳定增长的公司
    
    Analyze earnings consistency and growth.
    Buffett prefers companies with long-term stable growth
    """
    if len(financial_line_items) < 4:  # 趋势分析至少需要4个周期 - Need at least 4 periods for trend analysis
        return {"score": 0, "details": "Insufficient historical data"}

    score = 0
    reasoning = []

    # 检查盈利增长趋势 - Check earnings growth trend
    earnings_values = [item.net_income for item in financial_line_items if item.net_income]
    if len(earnings_values) >= 4:
        earnings_growth = all(earnings_values[i] > earnings_values[i + 1] for i in range(len(earnings_values) - 1))

        if earnings_growth:
            score += 3
            reasoning.append("Consistent earnings growth over past periods")
        else:
            reasoning.append("Inconsistent earnings growth pattern")

        # 计算增长率 - Calculate growth rate
        if len(earnings_values) >= 2:
            growth_rate = (earnings_values[0] - earnings_values[-1]) / abs(earnings_values[-1])
            reasoning.append(f"Total earnings growth of {growth_rate:.1%} over past {len(earnings_values)} periods")
    else:
        reasoning.append("Insufficient earnings data for trend analysis")

    return {
        "score": score,
        "details": "; ".join(reasoning),
    }


def calculate_owner_earnings(financial_line_items: list) -> dict[str, any]:
    """
    计算所有者收益（巴菲特偏好的真实盈利能力衡量指标）
    所有者收益 = 净收入 + 折旧 - 维护资本支出
    
    Calculate owner earnings (Buffett's preferred measure of true earnings power).
    Owner Earnings = Net Income + Depreciation - Maintenance CapEx
    """
    if not financial_line_items or len(financial_line_items) < 1:
        return {"owner_earnings": None, "details": ["Insufficient data for owner earnings calculation"]}

    latest = financial_line_items[0]

    # 获取所需组件 - Get required components
    net_income = latest.net_income
    depreciation = latest.depreciation_and_amortization
    capex = latest.capital_expenditure

    if not all([net_income, depreciation, capex]):
        return {"owner_earnings": None, "details": ["Missing components for owner earnings calculation"]}

    # 估算维护资本支出（通常是总资本支出的70-80%）
    # Estimate maintenance capex (typically 70-80% of total capex)
    maintenance_capex = capex * 0.75

    owner_earnings = net_income + depreciation - maintenance_capex

    return {
        "owner_earnings": owner_earnings,
        "components": {"net_income": net_income, "depreciation": depreciation, "maintenance_capex": maintenance_capex},
        "details": ["Owner earnings calculated successfully"],
    }


def calculate_intrinsic_value(financial_line_items: list) -> dict[str, any]:
    """
    使用基于所有者收益的DCF计算内在价值
    采用巴菲特式的保守假设进行估值
    
    Calculate intrinsic value using DCF with owner earnings.
    Uses conservative Buffett-style assumptions for valuation
    """
    if not financial_line_items:
        return {"value": None, "details": ["Insufficient data for valuation"]}

    # 计算所有者收益 - Calculate owner earnings
    earnings_data = calculate_owner_earnings(financial_line_items)
    if not earnings_data["owner_earnings"]:
        return {"value": None, "details": earnings_data["details"]}

    owner_earnings = earnings_data["owner_earnings"]

    # 获取当前市场数据 - Get current market data
    latest_financial_line_items = financial_line_items[0]
    shares_outstanding = latest_financial_line_items.outstanding_shares

    if not shares_outstanding:
        return {"value": None, "details": ["Missing shares outstanding data"]}

    # 巴菲特的DCF假设 - Buffett's DCF assumptions
    growth_rate = 0.05  # 保守的5%增长 - Conservative 5% growth
    discount_rate = 0.09  # 典型的9%折现率 - Typical 9% discount rate
    terminal_multiple = 12  # 保守的退出倍数 - Conservative exit multiple
    projection_years = 10

    # 计算未来价值 - Calculate future value
    future_value = 0
    for year in range(1, projection_years + 1):
        future_earnings = owner_earnings * (1 + growth_rate) ** year
        present_value = future_earnings / (1 + discount_rate) ** year
        future_value += present_value

    # 添加终值 - Add terminal value
    terminal_value = (owner_earnings * (1 + growth_rate) ** projection_years * terminal_multiple) / (1 + discount_rate) ** projection_years
    intrinsic_value = future_value + terminal_value

    return {
        "intrinsic_value": intrinsic_value,
        "owner_earnings": owner_earnings,
        "assumptions": {
            "growth_rate": growth_rate,
            "discount_rate": discount_rate,
            "terminal_multiple": terminal_multiple,
            "projection_years": projection_years,
        },
        "details": ["Intrinsic value calculated using DCF model with owner earnings"],
    }


# 移除了 model_name 和 model_provider 参数，因为模型固定为 GPT-4o
# Removed model_name and model_provider parameters as the model is fixed to GPT-4o
def generate_buffett_output(
    ticker: str,
    analysis_data: dict[str, any],
    # model_name: str, # 已移除 (Removed)
    # model_provider: str, # 已移除 (Removed)
) -> WarrenBuffettSignal:
    """
    基于巴菲特原则从LLM获取投资决策
    Get investment decision from LLM with Buffett's principles
    """
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是沃伦·巴菲特的人工智能代理。根据沃伦·巴菲特的原则确定投资信号：
                - 能力圈：只投资你了解的企业
                - 安全边际 (> 30%)：以低于内在价值的大幅折价买入
                - 经济护城河：寻找持久的竞争优势
                - 优质管理：寻求保守、以股东为导向的团队
                - 财务实力：青睐低负债、高股本回报率的企业
                - 长期视野：投资企业，而不仅仅是股票
                - 仅在基本面恶化或估值远超内在价值时出售

                在提供理由时，请做到详尽具体，具体如下：
                1. 解释对你决策影响最大的关键因素（正面和负面）
                2. 强调公司如何符合或违反特定的巴菲特原则
                3. 在相关之处提供量化证据（例如，具体的利润率、净资产收益率、债务水平）
                4. 最后以巴菲特式的评估方式对投资机会进行总结
                5. 在解释中运用沃伦·巴菲特的语气和对话风格

                例如，如果看涨："我对[特定优势]印象特别深刻，这让我们想起了我们早期对喜诗糖果的投资，当时我们看到了[类似的属性]……"
                例如，如果看跌："资本回报率的下降让我想起了伯克希尔哈撒韦的纺织业务，我们最终退出了，因为……"

                请严格遵循这些准则。
                """,
            ),
            (
                "human",
                """根据以下数据，像沃伦·巴菲特那样创建投资信号。

                股票{ticker} 的分析数据：
                {analysis_data}

                以以下 JSON 格式返回交易信号：
                {{
                  "signal": "买入/中性/卖出",
                  "confidence": float (0-100),
                  "reasoning": "string"
                }}
            """,
            ),
        ]
    )

    # 生成提示 - Generate the prompt
    prompt = template.invoke({
        "analysis_data": json.dumps(analysis_data, indent=2), 
        "ticker": ticker
      })

    # 创建WarrenBuffettSignal的默认工厂函数
    # Create default factory for WarrenBuffettSignal
    def create_default_warren_buffett_signal():
        """创建默认的Warren Buffett信号 - Create default Warren Buffett signal"""
        return WarrenBuffettSignal(signal="中性", confidence=0.0, reasoning="Error in analysis, defaulting to neutral")

    # 调用 call_llm 时不再传递 model_name 和 model_provider
    # model_name and model_provider are no longer passed when calling call_llm
    return call_llm(
        prompt=prompt, 
        # model_name=model_name, # 已移除 (Removed)
        # model_provider=model_provider, # 已移除 (Removed)
        pydantic_model=WarrenBuffettSignal, 
        agent_name="warren_buffett_agent", 
        default_factory=create_default_warren_buffett_signal,
        )
