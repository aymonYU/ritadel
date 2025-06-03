"""
沃伦·巴菲特价值投资分析师代理 - 基于巴菲特的投资原则
Warren Buffett value investing analyst agent - Based on Buffett's investment principles
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
    沃伦·巴菲特交易信号模型 - 包含投资信号、置信度和推理
    Warren Buffett trading signal model - Contains investment signal, confidence and reasoning

    该模型用于表示基于巴菲特投资原则的交易信号结果
    This model represents trading signal results based on Buffett's investment principles

    Attributes:
        signal: 交易信号，可以是买入、卖出或中性 / Trading signal: buy, sell or neutral
        confidence: 信号的置信度，范围0-100 / Signal confidence, range 0-100
        reasoning: 产生该信号的详细理由说明 / Detailed reasoning for the signal
    """
    signal: Literal["买入", "卖出", "中性"]
    confidence: float
    reasoning: str


def warren_buffett_agent(state: AgentState):
    """
    使用巴菲特的投资原则和LLM推理分析股票
    Analyzes stocks using Buffett's investment principles and LLM reasoning

    该函数实现了巴菲特的价值投资策略，通过分析公司的基本面、一致性、护城河、管理质量和内在价值
    来生成交易信号。
    This function implements Buffett's value investing strategy by analyzing company fundamentals,
    consistency, moat, management quality and intrinsic value to generate trading signals.

    Args:
        state (AgentState): 包含分析所需数据的状态对象，必须包含end_date和tickers
                           State object containing data needed for analysis, must include end_date and tickers

    Returns:
        dict: 包含每个股票的分析结果，包括交易信号、得分和详细分析数据
              Contains analysis results for each stock, including trading signals, scores and detailed analysis data
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    # 收集所有分析数据用于LLM推理 / Collect all analysis for LLM reasoning
    analysis_data = {}
    buffett_analysis = {}

    for ticker in tickers:
        progress.update_status("warren_buffett_agent", ticker, "Fetching financial metrics")
        # 获取所需数据 / Fetch required data
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
                "dividends_and_other_cash_distributions",
                "issuance_or_purchase_of_equity_shares",
            ],
            end_date,
        )

        progress.update_status("warren_buffett_agent", ticker, "Getting market cap")
        # 获取当前市值 / Get current market cap
        market_cap = get_market_cap(ticker, end_date)

        progress.update_status("warren_buffett_agent", ticker, "Analyzing fundamentals")
        # 分析基本面 / Analyze fundamentals
        fundamental_analysis = analyze_fundamentals(metrics)

        progress.update_status("warren_buffett_agent", ticker, "Analyzing consistency")
        consistency_analysis = analyze_consistency(financial_line_items)

        progress.update_status("warren_buffett_agent", ticker, "Analyzing moat")
        moat_analysis = analyze_moat(metrics)

        progress.update_status("warren_buffett_agent", ticker, "Analyzing management quality")
        mgmt_analysis = analyze_management_quality(financial_line_items)

        progress.update_status("warren_buffett_agent", ticker, "Calculating intrinsic value")
        intrinsic_value_analysis = calculate_intrinsic_value(financial_line_items)

        # 计算总分 / Calculate total score
        total_score = fundamental_analysis["score"] + consistency_analysis["score"] + moat_analysis["score"] + mgmt_analysis["score"]
        max_possible_score = 10 + moat_analysis["max_score"] + mgmt_analysis["max_score"]
        # fundamental_analysis + consistency combined were up to 10 points total
        # moat can add up to 3, mgmt can add up to 2, for example

        # 如果我们有内在价值和当前价格，添加安全边际分析 / Add margin of safety analysis if we have both intrinsic value and current price
        margin_of_safety = None
        intrinsic_value = intrinsic_value_analysis["intrinsic_value"]
        if intrinsic_value and market_cap:
            margin_of_safety = (intrinsic_value - market_cap) / market_cap

        # 使用更严格的安全边际要求生成交易信号 / Generate trading signal using a stricter margin-of-safety requirement
        # if fundamentals+moat+management are strong but margin_of_safety < 0.3, it's neutral
        # if fundamentals are very weak or margin_of_safety is severely negative -> bearish
        # else bullish
        if (total_score >= 0.7 * max_possible_score) and margin_of_safety and (margin_of_safety >= 0.3):
            signal = "买入"
        elif total_score <= 0.3 * max_possible_score or (margin_of_safety is not None and margin_of_safety < -0.3):
            # negative margin of safety beyond -30% could be overpriced -> bearish
            signal = "卖出"
        else:
            signal = "中性"

        # 合并所有分析结果 / Combine all analysis results
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "fundamental_analysis": fundamental_analysis,
            "consistency_analysis": consistency_analysis,
            "moat_analysis": moat_analysis,
            "management_analysis": mgmt_analysis,
            "intrinsic_value_analysis": intrinsic_value_analysis,
            "market_cap": market_cap,
            "margin_of_safety": margin_of_safety,
        }

        progress.update_status("warren_buffett_agent", ticker, "Generating Warren Buffett analysis")
        buffett_output = generate_buffett_output(
            ticker=ticker,
            analysis_data=analysis_data,
        )

        # 以与其他代理一致的格式存储分析 / Store analysis in consistent format with other agents
        buffett_analysis[ticker] = {
            "signal": buffett_output.signal,
            "confidence": buffett_output.confidence, # Normalize between 0 to 100
            "reasoning": buffett_output.reasoning,
        }

        progress.update_status("warren_buffett_agent", ticker, "Done")

    # 创建消息 / Create the message
    message = HumanMessage(content=json.dumps(buffett_analysis), name="warren_buffett_agent")

    # 如果请求显示推理过程 / Show reasoning if requested
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(buffett_analysis, "Warren Buffett Agent")

    # 将信号添加到analyst_signals列表 / Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["warren_buffett_agent"] = buffett_analysis

    return {"messages": [message], "data": state["data"]}


def analyze_fundamentals(metrics: list) -> dict[str, any]:
    """根据巴菲特的标准分析公司基本面 / Analyze company fundamentals based on Buffett's criteria."""
    if not metrics:
        return {"score": 0, "details": "基本面数据不足 / Insufficient fundamental data"}

    latest_metrics = metrics[0]

    score = 0
    reasoning = []

    # 检查ROE（净资产收益率）/ Check ROE (Return on Equity)
    roe = getattr(latest_metrics, 'return_on_equity', None)
    if roe and roe > 0.15:  # 15% ROE threshold
        score += 2
        reasoning.append(f"强劲的ROE：{roe:.1%} / Strong ROE of {roe:.1%}")
    elif roe:
        reasoning.append(f"较弱的ROE：{roe:.1%} / Weak ROE of {roe:.1%}")
    else:
        reasoning.append("ROE数据不可用 / ROE data not available")

    # 检查负债权益比 / Check Debt to Equity
    debt_to_equity = getattr(latest_metrics, 'debt_to_equity', None)
    if debt_to_equity and debt_to_equity < 0.5:
        score += 2
        reasoning.append("保守的债务水平 / Conservative debt levels")
    elif debt_to_equity:
        reasoning.append(f"较高的负债权益比：{debt_to_equity:.1f} / High debt to equity ratio of {debt_to_equity:.1f}")
    else:
        reasoning.append("负债权益比数据不可用 / Debt to equity data not available")

    # 检查营业利润率 / Check Operating Margin
    operating_margin = getattr(latest_metrics, 'operating_margin', None)
    if operating_margin and operating_margin > 0.15:
        score += 2
        reasoning.append("强劲的营业利润率 / Strong operating margins")
    elif operating_margin:
        reasoning.append(f"较弱的营业利润率：{operating_margin:.1%} / Weak operating margin of {operating_margin:.1%}")
    else:
        reasoning.append("营业利润率数据不可用 / Operating margin data not available")

    # 检查流动比率 / Check Current Ratio
    current_ratio = getattr(latest_metrics, 'current_ratio', None)
    if current_ratio and current_ratio > 1.5:
        score += 1
        reasoning.append("良好的流动性状况 / Good liquidity position")
    elif current_ratio:
        reasoning.append(f"较弱的流动性，流动比率为{current_ratio:.1f} / Weak liquidity with current ratio of {current_ratio:.1f}")
    else:
        reasoning.append("流动比率数据不可用 / Current ratio data not available")

    return {"score": score, "details": "; ".join(reasoning), "metrics": latest_metrics.model_dump()}


def analyze_consistency(financial_line_items: list) -> dict[str, any]:
    """分析盈利一致性和增长 / Analyze earnings consistency and growth."""
    if len(financial_line_items) < 4:  # 需要至少4个期间进行趋势分析 / Need at least 4 periods for trend analysis
        return {"score": 0, "details": "历史数据不足 / Insufficient historical data"}

    score = 0
    reasoning = []

    # 检查盈利增长趋势 / Check earnings growth trend
    earnings_values = [getattr(item, 'net_income', None) for item in financial_line_items if hasattr(item, 'net_income') and getattr(item, 'net_income', None)]
    if len(earnings_values) >= 4:
        # 简单检查：每个期间的盈利是否都比下一个大？/ Simple check: is each period's earnings bigger than the next?
        earnings_growth = all(earnings_values[i] > earnings_values[i + 1] for i in range(len(earnings_values) - 1))

        if earnings_growth:
            score += 3
            reasoning.append("过去几个期间盈利持续增长 / Consistent earnings growth over past periods")
        else:
            reasoning.append("盈利增长模式不一致 / Inconsistent earnings growth pattern")

        # 计算从最旧到最新的总增长率 / Calculate total growth rate from oldest to latest
        if len(earnings_values) >= 2 and earnings_values[-1] != 0:
            growth_rate = (earnings_values[0] - earnings_values[-1]) / abs(earnings_values[-1])
            reasoning.append(f"过去{len(earnings_values)}个期间的总盈利增长：{growth_rate:.1%} / Total earnings growth of {growth_rate:.1%} over past {len(earnings_values)} periods")
    else:
        reasoning.append("趋势分析的盈利数据不足 / Insufficient earnings data for trend analysis")

    return {
        "score": score,
        "details": "; ".join(reasoning),
    }


def analyze_moat(metrics: list) -> dict[str, any]:
    """
    评估公司是否可能拥有持续的竞争优势（护城河）。
    Evaluate whether the company likely has a durable competitive advantage (moat).
    
    为了简化，我们查看ROE/营业利润率在多个期间的稳定性
    或在过去几年的高利润率。更高的稳定性 => 更高的护城河得分。
    For simplicity, we look at stability of ROE/operating margins over multiple periods
    or high margin over the last few years. Higher stability => higher moat score.
    """
    if not metrics or len(metrics) < 3:
        return {"score": 0, "max_score": 3, "details": "护城河分析数据不足 / Insufficient data for moat analysis"}

    reasoning = []
    moat_score = 0
    historical_roes = []
    historical_margins = []

    for m in metrics:
        roe = getattr(m, 'return_on_equity', None)
        if roe is not None:
            historical_roes.append(roe)
        operating_margin = getattr(m, 'operating_margin', None)
        if operating_margin is not None:
            historical_margins.append(operating_margin)

    # 检查稳定或改善的ROE / Check for stable or improving ROE
    if len(historical_roes) >= 3:
        stable_roe = all(r > 0.15 for r in historical_roes)
        if stable_roe:
            moat_score += 1
            reasoning.append("各期间ROE稳定在15%以上（表明有护城河）/ Stable ROE above 15% across periods (suggests moat)")
        else:
            reasoning.append("ROE未持续保持在15%以上 / ROE not consistently above 15%")

    # 检查稳定或改善的营业利润率 / Check for stable or improving operating margin
    if len(historical_margins) >= 3:
        stable_margin = all(m > 0.15 for m in historical_margins)
        if stable_margin:
            moat_score += 1
            reasoning.append("营业利润率稳定在15%以上（护城河指标）/ Stable operating margins above 15% (moat indicator)")
        else:
            reasoning.append("营业利润率未持续保持在15%以上 / Operating margin not consistently above 15%")

    # 如果两者都稳定/改善，加一分 / If both are stable/improving, add an extra point
    if moat_score == 2:
        moat_score += 1
        reasoning.append("ROE和利润率的稳定性都表明有坚固的护城河 / Both ROE and margin stability indicate a solid moat")

    return {
        "score": moat_score,
        "max_score": 3,
        "details": "; ".join(reasoning),
    }


def analyze_management_quality(financial_line_items: list) -> dict[str, any]:
    """
    检查股份稀释或持续回购，以及一些股息记录。
    Checks for share dilution or consistent buybacks, and some dividend track record.
    
    简化方法：
    A simplified approach:
      - 如果有净股份回购或稳定的股份数量，这表明管理层可能对股东友好。
        if there's net share repurchase or stable share count, it suggests management
        might be shareholder-friendly.
      - 如果有大量新发行，可能是负面信号（稀释）。
        if there's a big new issuance, it might be a negative sign (dilution).
    """
    if not financial_line_items:
        return {"score": 0, "max_score": 2, "details": "管理层分析数据不足 / Insufficient data for management analysis"}

    reasoning = []
    mgmt_score = 0

    latest = financial_line_items[0]
    equity_issuance = getattr(latest, "issuance_or_purchase_of_equity_shares", None)
    if equity_issuance and equity_issuance < 0:
        # 负值意味着公司在回购上花钱 / Negative means the company spent money on buybacks
        mgmt_score += 1
        reasoning.append("公司一直在回购股票（对股东友好）/ Company has been repurchasing shares (shareholder-friendly)")

    if equity_issuance and equity_issuance > 0:
        # 正发行意味着新股份 => 可能稀释 / Positive issuance means new shares => possible dilution
        reasoning.append("最近有普通股发行（潜在稀释）/ Recent common stock issuance (potential dilution)")
    else:
        reasoning.append("未检测到重大新股发行 / No significant new stock issuance detected")

    # 检查任何股息 / Check for any dividends
    dividends = getattr(latest, "dividends_and_other_cash_distributions", None)
    if dividends and dividends < 0:
        mgmt_score += 1
        reasoning.append("公司有支付股息的记录 / Company has a track record of paying dividends")
    else:
        reasoning.append("无股息或最小股息支付 / No or minimal dividends paid")

    return {
        "score": mgmt_score,
        "max_score": 2,
        "details": "; ".join(reasoning),
    }


def calculate_owner_earnings(financial_line_items: list) -> dict[str, any]:
    """
    计算所有者收益（巴菲特偏好的真实盈利能力衡量）。
    Calculate owner earnings (Buffett's preferred measure of true earnings power).
    所有者收益 = 净利润 + 折旧 - 维护资本支出
    Owner Earnings = Net Income + Depreciation - Maintenance CapEx
    """
    if not financial_line_items or len(financial_line_items) < 1:
        return {"owner_earnings": None, "details": ["所有者收益计算数据不足 / Insufficient data for owner earnings calculation"]}

    latest = financial_line_items[0]

    net_income = getattr(latest, 'net_income', None)
    depreciation = getattr(latest, 'depreciation_and_amortization', None)
    capex = getattr(latest, 'capital_expenditure', None)

    if not all([net_income, depreciation, capex]):
        return {"owner_earnings": None, "details": ["所有者收益计算缺少组件 / Missing components for owner earnings calculation"]}

    # 估计维护资本支出（通常是总资本支出的70-80%）/ Estimate maintenance capex (typically 70-80% of total capex)
    maintenance_capex = capex * 0.75
    owner_earnings = net_income + depreciation - maintenance_capex

    return {
        "owner_earnings": owner_earnings,
        "components": {"net_income": net_income, "depreciation": depreciation, "maintenance_capex": maintenance_capex},
        "details": ["所有者收益计算成功 / Owner earnings calculated successfully"],
    }


def calculate_intrinsic_value(financial_line_items: list) -> dict[str, any]:
    """使用所有者收益的DCF计算内在价值 / Calculate intrinsic value using DCF with owner earnings."""
    if not financial_line_items:
        return {"intrinsic_value": None, "details": ["估值数据不足 / Insufficient data for valuation"]}

    # 计算所有者收益 / Calculate owner earnings
    earnings_data = calculate_owner_earnings(financial_line_items)
    if not earnings_data["owner_earnings"]:
        return {"intrinsic_value": None, "details": earnings_data["details"]}

    owner_earnings = earnings_data["owner_earnings"]

    # 获取当前市场数据 / Get current market data
    latest_financial_line_items = financial_line_items[0]
    shares_outstanding = getattr(latest_financial_line_items, 'outstanding_shares', None)

    if not shares_outstanding:
        return {"intrinsic_value": None, "details": ["缺少流通股数据 / Missing shares outstanding data"]}

    # 巴菲特的DCF假设（保守方法）/ Buffett's DCF assumptions (conservative approach)
    growth_rate = 0.05  # 保守的5%增长 / Conservative 5% growth
    discount_rate = 0.09  # 典型的~9%折现率 / Typical ~9% discount rate
    terminal_multiple = 12
    projection_years = 10

    # 折现未来所有者收益的总和 / Sum of discounted future owner earnings
    future_value = 0
    for year in range(1, projection_years + 1):
        future_earnings = owner_earnings * (1 + growth_rate) ** year
        present_value = future_earnings / (1 + discount_rate) ** year
        future_value += present_value

    # 终值 / Terminal value
    terminal_value = (owner_earnings * (1 + growth_rate) ** projection_years * terminal_multiple) / ((1 + discount_rate) ** projection_years)

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
        "details": ["使用所有者收益的DCF模型计算内在价值 / Intrinsic value calculated using DCF model with owner earnings"],
    }


def generate_buffett_output(
    ticker: str,
    analysis_data: dict[str, any],
) -> WarrenBuffettSignal:
    """基于巴菲特原则从LLM获取投资决策 / Get investment decision from LLM with Buffett's principles"""
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是沃伦·巴菲特的人工智能代理。根据沃伦·巴菲特的原则决定投资信号：
                - 能力圈：只投资你了解的企业
                - 安全边际（> 30%）：以显著低于内在价值的价格买入
                - 经济护城河：寻找持续的竞争优势
                - 优质管理：寻求保守的、以股东为导向的团队
                - 财务实力：偏好低债务、强净资产收益率
                - 长期视野：投资企业，而不仅仅是股票
                - 只有在基本面恶化或估值远超内在价值时才卖出

                当提供你的推理时，要彻底和具体，通过：
                1. 解释最影响你决定的关键因素（包括正面和负面的）
                2. 强调公司如何符合或违反特定的巴菲特原则
                3. 在相关处提供定量证据（例如，具体的利润率、ROE值、债务水平）
                4. 以巴菲特式的投资机会评估作结
                5. 在你的解释中使用沃伦·巴菲特的语调和对话风格

                例如，如果看涨："我特别对[具体优势]印象深刻，让我想起了我们早期投资喜诗糖果时看到的[类似属性]..."
                例如，如果看跌："资本回报率的下降让我想起了伯克希尔的纺织业务，我们最终退出了，因为..."

                严格按照这些指导原则。

                严格按照以下JSON格式返回交易信号：
                {{
                  "signal": "买入" | "卖出" | "中性",
                  "confidence": 0到100之间的浮点数,
                  "reasoning": "字符串"
                }}
                """,
            ),
            (
                "human",
                """基于以下数据，创建沃伦·巴菲特会做出的投资信号：

                {ticker}的分析数据：
                {analysis_data}

                完全按照以下JSON格式返回交易信号：
                {{
                  "signal": "买入" | "卖出" | "中性",
                  "confidence": 0到100之间的浮点数,
                  "reasoning": "字符串"
                }}
                """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    # 解析失败时的默认后备信号 / Default fallback signal in case parsing fails
    def create_default_warren_buffett_signal():
        return WarrenBuffettSignal(signal="中性", confidence=0.0, reasoning="分析错误，默认为中性 / Error in analysis, defaulting to neutral")

    return call_llm(
        prompt=prompt,
        pydantic_model=WarrenBuffettSignal,
        agent_name="warren_buffett_agent",
        default_factory=create_default_warren_buffett_signal,
    )
