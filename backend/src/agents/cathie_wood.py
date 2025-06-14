from langchain_openai import ChatOpenAI
from graph.state import AgentState, show_agent_reasoning
from tools.api import get_financial_metrics, get_market_cap, search_line_items
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm

"""
Cathie Wood颠覆性创新分析师代理 - 基于凯西·伍德的颠覆性创新投资策略
Cathie Wood disruptive innovation analyst agent - Based on Cathie Wood's disruptive innovation investment strategy
"""

class CathieWoodSignal(BaseModel):
    """
    凯西·伍德分析信号模型 - 包含投资信号、置信度和推理
    Cathie Wood analysis signal model - Contains investment signal, confidence and reasoning
    """
    signal: Literal["买入", "卖出", "中性"]
    confidence: float
    reasoning: str


def cathie_wood_agent(state: AgentState):
    """
    使用凯西·伍德的投资原则和LLM推理分析股票
    伍德的核心投资理念：
    1. 优先考虑具有突破性技术或商业模式的公司
    2. 专注于具有快速采用曲线和巨大TAM（总可寻址市场）的行业
    3. 主要投资于AI、机器人、基因测序、金融科技和区块链
    4. 愿意承受短期波动以获得长期收益
    5. 寻找正在改变世界的颠覆性创新企业
    
    Analyzes stocks using Cathie Wood's investing principles and LLM reasoning.
    Wood's core investment philosophy:
    1. Prioritizes companies with breakthrough technologies or business models
    2. Focuses on industries with rapid adoption curves and massive TAM (Total Addressable Market).
    3. Invests mostly in AI, robotics, genomic sequencing, fintech, and blockchain.
    4. Willing to endure short-term volatility for long-term gains.
    5. Seeks disruptive innovation companies that are changing the world
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    # 收集分析数据 - Collect analysis data
    analysis_data = {}
    cw_analysis = {}

    for ticker in tickers:
        progress.update_status("cathie_wood_agent", ticker, "Fetching financial metrics")
        # 可以调整这些参数（period="annual"/"ttm", limit=5/10等）
        # You can adjust these parameters (period="annual"/"ttm", limit=5/10, etc.)
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=5)

        progress.update_status("cathie_wood_agent", ticker, "Gathering financial line items")
        # 请求多个时期的数据（年度或TTM）以获得更强健的视图
        # Request multiple periods of data (annual or TTM) for a more robust view.
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",  # 收入
                "gross_margin",  # 毛利率
                "operating_margin",  # 营业利润率
                "debt_to_equity",  # 债务股权比
                "free_cash_flow",  # 自由现金流
                "total_assets",  # 总资产
                "total_liabilities",  # 总负债
                "dividends_and_other_cash_distributions",  # 分红和其他现金分配
                "outstanding_shares",  # 流通股数
                "research_and_development",  # 研发费用
                "capital_expenditure",  # 资本支出
                "operating_expense",  # 运营费用
            ],
            end_date,
            period="annual",
            limit=5
        )

        progress.update_status("cathie_wood_agent", ticker, "Getting market cap")
        market_cap = get_market_cap(ticker, end_date)

        progress.update_status("cathie_wood_agent", ticker, "Analyzing disruptive potential")
        # 分析颠覆性潜力 - Analyze disruptive potential
        disruptive_analysis = analyze_disruptive_potential(metrics, financial_line_items)

        progress.update_status("cathie_wood_agent", ticker, "Analyzing innovation-driven growth")
        # 分析创新驱动的增长 - Analyze innovation-driven growth
        innovation_analysis = analyze_innovation_growth(metrics, financial_line_items)

        progress.update_status("cathie_wood_agent", ticker, "Calculating valuation & high-growth scenario")
        # 计算估值和高增长情景 - Calculate valuation & high-growth scenario
        valuation_analysis = analyze_cathie_wood_valuation(financial_line_items, market_cap)

        # 合并部分评分或信号 - Combine partial scores or signals
        total_score = disruptive_analysis["score"] + innovation_analysis["score"] + valuation_analysis["score"]
        max_possible_score = 15  # 根据需要调整权重 - Adjust weighting as desired

        if total_score >= 0.7 * max_possible_score:
            signal = "bullish"
        elif total_score <= 0.3 * max_possible_score:
            signal = "bearish"
        else:
            signal = "neutral"

        # 整合所有分析数据 - Combine all analysis data
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "disruptive_analysis": disruptive_analysis,
            "innovation_analysis": innovation_analysis,
            "valuation_analysis": valuation_analysis
        }

        progress.update_status("cathie_wood_agent", ticker, "Generating Cathie Wood style analysis")
        cw_output = generate_cathie_wood_output(
            ticker=ticker,
            analysis_data=analysis_data,
        )

        cw_analysis[ticker] = {
            "signal": cw_output.signal,
            "confidence": cw_output.confidence,
            "reasoning": cw_output.reasoning
        }

        progress.update_status("cathie_wood_agent", ticker, "Done")

    # 将结果包装在单个消息中 - Wrap results in a single message
    message = HumanMessage(
        content=json.dumps(cw_analysis),
        name="cathie_wood_agent"
    )

    # 如果请求，显示推理过程 - Show reasoning if requested
    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(cw_analysis, "Cathie Wood Agent")

    # 将信号添加到整体状态 - Add signals to the overall state
    state["data"]["analyst_signals"]["cathie_wood_agent"] = cw_analysis

    return {
        "messages": [message],
        "data": state["data"]
    }


def analyze_disruptive_potential(metrics: list, financial_line_items: list) -> dict:
    """
    分析公司是否具有颠覆性产品、技术或商业模式
    评估颠覆性潜力的多个维度：
    1. 收入增长加速 - 表明市场采用情况
    2. 研发强度 - 显示创新投资水平
    3. 毛利率趋势 - 暗示定价权和可扩展性
    4. 运营杠杆 - 展示商业模式效率
    5. 市场份额动态 - 表明竞争地位
    
    Analyze whether the company has disruptive products, technology, or business model.
    Evaluates multiple dimensions of disruptive potential:
    1. Revenue Growth Acceleration - indicates market adoption
    2. R&D Intensity - shows innovation investment
    3. Gross Margin Trends - suggests pricing power and scalability
    4. Operating Leverage - demonstrates business model efficiency
    5. Market Share Dynamics - indicates competitive position
    """
    score = 0
    details = []

    if not metrics or not financial_line_items:
        return {
            "score": 0,
            "details": "Insufficient data to analyze disruptive potential"
        }

    # 1. 收入增长分析 - 检查增长加速情况 - Revenue Growth Analysis - Check for accelerating growth
    revenues = [item.revenue for item in financial_line_items if item.revenue]
    if len(revenues) >= 2:  # 降低从3个期间到2个期间的要求 / Lower requirement from 3 to 2 periods
        if len(revenues) >= 3:
            # 3个或更多期间：进行增长加速分析 / 3+ periods: perform growth acceleration analysis
            growth_rates = []
            for i in range(len(revenues)-1):
                if revenues[i] and revenues[i+1]:
                    growth_rate = (revenues[i+1] - revenues[i]) / abs(revenues[i]) if revenues[i] != 0 else 0
                    growth_rates.append(growth_rate)

            # 检查增长是否在加速 - Check if growth is accelerating
            if len(growth_rates) >= 2 and growth_rates[-1] > growth_rates[0]:
                score += 2
                details.append(f"Revenue growth is accelerating: {(growth_rates[-1]*100):.1f}% vs {(growth_rates[0]*100):.1f}%")

            # 检查绝对增长率 - Check absolute growth rate
            latest_growth = growth_rates[-1] if growth_rates else 0
            if latest_growth > 1.0:  # 超过100%的增长 - Over 100% growth
                score += 3
                details.append(f"Exceptional revenue growth: {(latest_growth*100):.1f}%")
            elif latest_growth > 0.5:  # 50%以上增长 - Over 50% growth
                score += 2
                details.append(f"Strong revenue growth: {(latest_growth*100):.1f}%")
            elif latest_growth > 0.2:  # 20%以上增长 - Over 20% growth
                score += 1
                details.append(f"Moderate revenue growth: {(latest_growth*100):.1f}%")
        else:
            # 只有2个期间：基础增长分析 / Only 2 periods: basic growth analysis
            if revenues[0] and revenues[1] and revenues[1] != 0:
                growth_rate = (revenues[0] - revenues[1]) / abs(revenues[1])
                if growth_rate > 1.0:  # 超过100%的增长
                    score += 2
                    details.append(f"Exceptional revenue growth (limited data): {(growth_rate*100):.1f}%")
                elif growth_rate > 0.5:  # 50%以上增长
                    score += 1
                    details.append(f"Strong revenue growth (limited data): {(growth_rate*100):.1f}%")
                elif growth_rate > 0.2:  # 20%以上增长
                    details.append(f"Moderate revenue growth (limited data): {(growth_rate*100):.1f}%")
                else:
                    details.append(f"Limited revenue growth (limited data): {(growth_rate*100):.1f}%")
    else:
        details.append("Insufficient revenue data for growth analysis")

    # 2. 毛利率分析 - 检查毛利率扩张情况 - Gross Margin Analysis - Check for expanding margins
    gross_margins = [item.gross_margin for item in financial_line_items if hasattr(item, 'gross_margin') and item.gross_margin is not None]
    if len(gross_margins) >= 2:
        margin_trend = gross_margins[-1] - gross_margins[0]
        if margin_trend > 0.05:  # 5%的改善 - 5% improvement
            score += 2
            details.append(f"Expanding gross margins: +{(margin_trend*100):.1f}%")
        elif margin_trend > 0:
            score += 1
            details.append(f"Slightly improving gross margins: +{(margin_trend*100):.1f}%")

        # 检查绝对毛利率水平 - Check absolute margin level
        if gross_margins[-1] > 0.50:  # 高毛利率业务 - High margin business
            score += 2
            details.append(f"High gross margin: {(gross_margins[-1]*100):.1f}%")
    else:
        details.append("Insufficient gross margin data")

    # 3. 运营杠杆分析 - Operating Leverage Analysis
    revenues = [item.revenue for item in financial_line_items if item.revenue]
    operating_expenses = [
        item.operating_expense
        for item in financial_line_items
        if hasattr(item, "operating_expense") and item.operating_expense
    ]

    if len(revenues) >= 2 and len(operating_expenses) >= 2:
        rev_growth = (revenues[-1] - revenues[0]) / abs(revenues[0])
        opex_growth = (operating_expenses[-1] - operating_expenses[0]) / abs(operating_expenses[0])

        if rev_growth > opex_growth:
            score += 2
            details.append("Positive operating leverage: Revenue growing faster than expenses")
    else:
        details.append("Insufficient data for operating leverage analysis")

    # 4. R&D Investment Analysis
    rd_expenses = [item.research_and_development for item in financial_line_items if hasattr(item, 'research_and_development') and item.research_and_development is not None]
    if rd_expenses and revenues:
        rd_intensity = rd_expenses[-1] / revenues[-1]
        if rd_intensity > 0.15:  # High R&D intensity
            score += 3
            details.append(f"High R&D investment: {(rd_intensity*100):.1f}% of revenue")
        elif rd_intensity > 0.08:
            score += 2
            details.append(f"Moderate R&D investment: {(rd_intensity*100):.1f}% of revenue")
        elif rd_intensity > 0.05:
            score += 1
            details.append(f"Some R&D investment: {(rd_intensity*100):.1f}% of revenue")
    else:
        details.append("No R&D data available")

    # Normalize score to be out of 5
    max_possible_score = 12  # Sum of all possible points
    normalized_score = (score / max_possible_score) * 5

    return {
        "score": normalized_score,
        "details": "; ".join(details),
        "raw_score": score,
        "max_score": max_possible_score
    }


def analyze_innovation_growth(metrics: list, financial_line_items: list) -> dict:
    """
    Evaluate the company's commitment to innovation and potential for exponential growth.
    Analyzes multiple dimensions:
    1. R&D Investment Trends - measures commitment to innovation
    2. Free Cash Flow Generation - indicates ability to fund innovation
    3. Operating Efficiency - shows scalability of innovation
    4. Capital Allocation - reveals innovation-focused management
    5. Growth Reinvestment - demonstrates commitment to future growth
    """
    score = 0
    details = []

    if not metrics or not financial_line_items:
        return {
            "score": 0,
            "details": "Insufficient data to analyze innovation-driven growth"
        }

    # 1. R&D Investment Trends
    rd_expenses = [
        item.research_and_development
        for item in financial_line_items
        if hasattr(item, "research_and_development") and item.research_and_development
    ]
    revenues = [item.revenue for item in financial_line_items if item.revenue]

    if rd_expenses and revenues and len(rd_expenses) >= 2:
        # Check R&D growth rate
        rd_growth = (rd_expenses[-1] - rd_expenses[0]) / abs(rd_expenses[0]) if rd_expenses[0] != 0 else 0
        if rd_growth > 0.5:  # 50% growth in R&D
            score += 3
            details.append(f"Strong R&D investment growth: +{(rd_growth*100):.1f}%")
        elif rd_growth > 0.2:
            score += 2
            details.append(f"Moderate R&D investment growth: +{(rd_growth*100):.1f}%")

        # Check R&D intensity trend
        rd_intensity_start = rd_expenses[0] / revenues[0]
        rd_intensity_end = rd_expenses[-1] / revenues[-1]
        if rd_intensity_end > rd_intensity_start:
            score += 2
            details.append(f"Increasing R&D intensity: {(rd_intensity_end*100):.1f}% vs {(rd_intensity_start*100):.1f}%")
    else:
        details.append("Insufficient R&D data for trend analysis")

    # 2. Free Cash Flow Analysis
    fcf_vals = [item.free_cash_flow for item in financial_line_items if hasattr(item, 'free_cash_flow') and item.free_cash_flow is not None]
    if fcf_vals and len(fcf_vals) >= 2:
        # Check FCF growth and consistency
        fcf_growth = (fcf_vals[-1] - fcf_vals[0]) / abs(fcf_vals[0])
        positive_fcf_count = sum(1 for f in fcf_vals if f > 0)

        if fcf_growth > 0.3 and positive_fcf_count == len(fcf_vals):
            score += 3
            details.append("Strong and consistent FCF growth, excellent innovation funding capacity")
        elif positive_fcf_count >= len(fcf_vals) * 0.75:
            score += 2
            details.append("Consistent positive FCF, good innovation funding capacity")
        elif positive_fcf_count > len(fcf_vals) * 0.5:
            score += 1
            details.append("Moderately consistent FCF, adequate innovation funding capacity")
    else:
        details.append("Insufficient FCF data for analysis")

    # 3. Operating Efficiency Analysis
    op_margin_vals = [item.operating_margin for item in financial_line_items 
                     if hasattr(item, 'operating_margin') and item.operating_margin is not None]
    
    if op_margin_vals and len(op_margin_vals) >= 2:
        # Check margin improvement
        margin_trend = op_margin_vals[-1] - op_margin_vals[0]

        if op_margin_vals[-1] > 0.15 and margin_trend > 0:
            score += 3
            details.append(f"Strong and improving operating margin: {(op_margin_vals[-1]*100):.1f}%")
        elif op_margin_vals[-1] > 0.10:
            score += 2
            details.append(f"Healthy operating margin: {(op_margin_vals[-1]*100):.1f}%")
        elif margin_trend > 0:
            score += 1
            details.append("Improving operating efficiency")
    else:
        details.append("Insufficient operating margin data")

    # 4. Capital Allocation Analysis
    capex = [item.capital_expenditure for item in financial_line_items if hasattr(item, 'capital_expenditure') and item.capital_expenditure]
    if capex and revenues and len(capex) >= 2:
        capex_intensity = abs(capex[-1]) / revenues[-1]
        capex_growth = (abs(capex[-1]) - abs(capex[0])) / abs(capex[0]) if capex[0] != 0 else 0

        if capex_intensity > 0.10 and capex_growth > 0.2:
            score += 2
            details.append("Strong investment in growth infrastructure")
        elif capex_intensity > 0.05:
            score += 1
            details.append("Moderate investment in growth infrastructure")
    else:
        details.append("Insufficient CAPEX data")

    # 5. Growth Reinvestment Analysis
    dividends = [item.dividends_and_other_cash_distributions for item in financial_line_items if hasattr(item, 'dividends_and_other_cash_distributions') and item.dividends_and_other_cash_distributions]
    if dividends and fcf_vals:
        # Check if company prioritizes reinvestment over dividends
        latest_payout_ratio = dividends[-1] / fcf_vals[-1] if fcf_vals[-1] != 0 else 1
        if latest_payout_ratio < 0.2:  # Low dividend payout ratio suggests reinvestment focus
            score += 2
            details.append("Strong focus on reinvestment over dividends")
        elif latest_payout_ratio < 0.4:
            score += 1
            details.append("Moderate focus on reinvestment over dividends")
    else:
        details.append("Insufficient dividend data")

    # Normalize score to be out of 5
    max_possible_score = 15  # Sum of all possible points
    normalized_score = (score / max_possible_score) * 5

    return {
        "score": normalized_score,
        "details": "; ".join(details),
        "raw_score": score,
        "max_score": max_possible_score
    }


def analyze_cathie_wood_valuation(financial_line_items: list, market_cap: float) -> dict:
    """
    Cathie Wood often focuses on long-term exponential growth potential. We can do
    a simplified approach looking for a large total addressable market (TAM) and the
    company's ability to capture a sizable portion.
    """
    if not financial_line_items or market_cap is None:
        return {
            "score": 0,
            "details": "Insufficient data for valuation"
        }

    latest = financial_line_items[-1]
    fcf = latest.free_cash_flow if latest.free_cash_flow else 0

    if fcf <= 0:
        return {
            "score": 0,
            "details": f"No positive FCF for valuation; FCF = {fcf}",
            "intrinsic_value": None
        }

    # Instead of a standard DCF, let's assume a higher growth rate for an innovative company.
    # Example values:
    growth_rate = 0.20  # 20% annual growth
    discount_rate = 0.15
    terminal_multiple = 25
    projection_years = 5

    present_value = 0
    for year in range(1, projection_years + 1):
        future_fcf = fcf * (1 + growth_rate) ** year
        pv = future_fcf / ((1 + discount_rate) ** year)
        present_value += pv

    # Terminal Value
    terminal_value = (fcf * (1 + growth_rate) ** projection_years * terminal_multiple) \
                     / ((1 + discount_rate) ** projection_years)
    intrinsic_value = present_value + terminal_value

    margin_of_safety = (intrinsic_value - market_cap) / market_cap

    score = 0
    if margin_of_safety > 0.5:
        score += 3
    elif margin_of_safety > 0.2:
        score += 1

    details = [
        f"Calculated intrinsic value: ~{intrinsic_value:,.2f}",
        f"Market cap: ~{market_cap:,.2f}",
        f"Margin of safety: {margin_of_safety:.2%}"
    ]

    return {
        "score": score,
        "details": "; ".join(details),
        "intrinsic_value": intrinsic_value,
        "margin_of_safety": margin_of_safety
    }


# 移除了 model_name 和 model_provider 参数，因为模型固定为 GPT-4o
# Removed model_name and model_provider parameters as the model is fixed to GPT-4o
def generate_cathie_wood_output(
    ticker: str,
    analysis_data: dict[str, any],
    # model_name: str, # 已移除 (Removed)
    # model_provider: str, # 已移除 (Removed)
) -> CathieWoodSignal:
    """
    Generates investment decisions in the style of Cathie Wood.
    """
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是凯西·伍德的 AI 智能体，运用她的原则进行投资决策：
            
            "1. 寻找能够利用颠覆性创新的公司。"
            "2. 强调指数级增长潜力和巨大的潜在市场。"
            "3. 专注于科技、医疗保健或其他面向未来的行业。"
            "4. 考虑多年的投资期限以寻找潜在的突破。"
            "5. 为追求高回报，接受更高的波动性。"
            "6. 评估管理层的愿景和研发投资能力。"
            "规则："
            "- 识别颠覆性或突破性技术。"
            "- 评估多年收入增长的强劲潜力。"
            "- 检查公司是否能够在大型市场中有效扩展。"
            "- 使用增长导向的估值方法。"
            "- 提供数据驱动的建议（买入/卖出/中性）。"""
        ),
        (
            "human",
                """根据以下数据，像凯西·伍德那样创建投资信号。

                股票{ticker} 的分析数据:
                {analysis_data}

                按照此格式返回 JSON:
                {{
                  "signal": "买入/中性/卖出",
                  "confidence": float (0-100),
                  "reasoning": "string"
                }}
            """,
        )
    ])

    prompt = template.invoke({
        "analysis_data": json.dumps(analysis_data, indent=2),
        "ticker": ticker
    })

    def create_default_cathie_wood_signal():
        return CathieWoodSignal(
            signal="中性",
            confidence=0.0,
            reasoning="Error in analysis, defaulting to neutral"
        )

    # 调用 call_llm 时不再传递 model_name 和 model_provider
    # model_name and model_provider are no longer passed when calling call_llm
    return call_llm(
        prompt=prompt,
        # model_name=model_name, # 已移除 (Removed)
        # model_provider=model_provider, # 已移除 (Removed)
        pydantic_model=CathieWoodSignal,
        agent_name="cathie_wood_agent",
        default_factory=create_default_cathie_wood_signal,
    )

# source: https://ark-invest.com