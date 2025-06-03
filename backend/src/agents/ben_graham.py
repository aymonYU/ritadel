"""
Ben Graham价值投资分析师代理 - 基于本杰明·格雷厄姆的价值投资原则
Ben Graham value investing analyst agent - Based on Benjamin Graham's value investing principles
"""
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
import math


class BenGrahamSignal(BaseModel):
    """
    Ben Graham分析信号模型 - 包含投资信号、置信度和推理
    Ben Graham analysis signal model - Contains investment signal, confidence and reasoning
    """
    signal: Literal["买入", "卖出", "中性"]
    confidence: float
    reasoning: str


def ben_graham_agent(state: AgentState):
    """
    使用本杰明·格雷厄姆的经典价值投资原则分析股票：
    Analyzes stocks using Benjamin Graham's classic value-investing principles:
    1. 多年的收益稳定性 - Earnings stability over multiple years.
    2. 强劲的财务实力（低债务，充足的流动性）- Solid financial strength (low debt, adequate liquidity).
    3. 相对于内在价值的折扣（例如格雷厄姆数字或net-net）- Discount to intrinsic value (e.g. Graham Number or net-net).
    4. 充足的安全边际 - Adequate margin of safety.
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    analysis_data = {}
    graham_analysis = {}

    for ticker in tickers:
        progress.update_status("ben_graham_agent", ticker, "Fetching financial metrics")
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=10)

        progress.update_status("ben_graham_agent", ticker, "Gathering financial line items")
        financial_line_items = search_line_items(ticker, ["earnings_per_share", "revenue", "net_income", "book_value_per_share", "total_assets", "total_liabilities", "current_assets", "current_liabilities", "dividends_and_other_cash_distributions", "outstanding_shares"], end_date, period="annual", limit=10)

        progress.update_status("ben_graham_agent", ticker, "Getting market cap")
        market_cap = get_market_cap(ticker, end_date)

        # 执行子分析 - Perform sub-analyses
        progress.update_status("ben_graham_agent", ticker, "Analyzing earnings stability")
        earnings_analysis = analyze_earnings_stability(metrics, financial_line_items)

        progress.update_status("ben_graham_agent", ticker, "Analyzing financial strength")
        strength_analysis = analyze_financial_strength(metrics, financial_line_items)

        progress.update_status("ben_graham_agent", ticker, "Analyzing Graham valuation")
        valuation_analysis = analyze_valuation_graham(metrics, financial_line_items, market_cap)

        # 聚合评分 - Aggregate scoring
        total_score = earnings_analysis["score"] + strength_analysis["score"] + valuation_analysis["score"]
        max_possible_score = 15  # total possible from the three analysis functions

        # 将总分映射到信号 - Map total_score to signal
        if total_score >= 0.7 * max_possible_score:
            signal = "买入"
        elif total_score <= 0.3 * max_possible_score:
            signal = "卖出"
        else:
            signal = "中性"

        analysis_data[ticker] = {"signal": signal, "score": total_score, "max_score": max_possible_score, "earnings_analysis": earnings_analysis, "strength_analysis": strength_analysis, "valuation_analysis": valuation_analysis}

        progress.update_status("ben_graham_agent", ticker, "Generating Graham-style analysis")
        graham_output = generate_graham_output(
            ticker=ticker,
            analysis_data=analysis_data,
        )

        graham_analysis[ticker] = {"signal": graham_output.signal, "confidence": graham_output.confidence, "reasoning": graham_output.reasoning}

        progress.update_status("ben_graham_agent", ticker, "Done")

    # 将结果包装在单个消息中以供链式传递
    # Wrap results in a single message for the chain
    message = HumanMessage(content=json.dumps(graham_analysis), name="ben_graham_agent")

    # 可选择显示推理过程 - Optionally display reasoning
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(graham_analysis, "Ben Graham Agent")

    # 在整体状态中存储信号 - Store signals in the overall state
    state["data"]["analyst_signals"]["ben_graham_agent"] = graham_analysis

    return {"messages": [message], "data": state["data"]}


def analyze_earnings_stability(metrics: list, financial_line_items: list) -> dict:
    """
    分析收益稳定性
    格雷厄姆希望至少连续几年的正收益（理想情况下5+年）。
    我们将检查：
    1. 正EPS的年数。
    2. EPS从第一期到最后一期的增长。
    
    Analyze earnings stability
    Graham wants at least several years of consistently positive earnings (ideally 5+).
    We'll check:
    1. Number of years with positive EPS.
    2. Growth in EPS from first to last period.
    """
    score = 0
    details = []

    if not metrics or not financial_line_items:
        return {"score": score, "details": "Insufficient data for earnings stability analysis"}

    eps_vals = []
    for item in financial_line_items:
        if hasattr(item, 'earnings_per_share') and item.earnings_per_share is not None:
            eps_vals.append(item.earnings_per_share)

    if len(eps_vals) < 2:
        details.append("Not enough multi-year EPS data.")
        return {"score": score, "details": "; ".join(details)}

    # 1. 持续正EPS - Consistently positive EPS
    positive_eps_years = sum(1 for e in eps_vals if e > 0)
    total_eps_years = len(eps_vals)
    if positive_eps_years == total_eps_years:
        score += 3
        details.append("EPS was positive in all available periods.")
    elif positive_eps_years >= (total_eps_years * 0.8):
        score += 2
        details.append("EPS was positive in most periods.")
    else:
        details.append("EPS was negative in multiple periods.")

    # 2. EPS从最早到最新的增长 - EPS growth from earliest to latest
    if eps_vals[-1] > eps_vals[0]:
        score += 1
        details.append("EPS grew from earliest to latest period.")
    else:
        details.append("EPS did not grow from earliest to latest period.")

    return {"score": score, "details": "; ".join(details)}


def analyze_financial_strength(metrics: list, financial_line_items: list) -> dict:
    """
    分析财务实力
    格雷厄姆检查流动性（流动比率 >= 2），可管理的债务，
    以及整体财务保守性。
    
    Analyze financial strength
    Graham checks liquidity (current ratio >= 2), manageable debt,
    and overall financial conservatism.
    """
    score = 0
    details = []

    if not financial_line_items:
        return {"score": score, "details": "Insufficient data for financial strength analysis"}

    latest_item = financial_line_items[0]

    # 1. 流动比率 - Current Ratio
    # Make sure the attributes exist before trying to use them
    current_assets = 0
    current_liabilities = 0
    
    if hasattr(latest_item, 'current_assets') and latest_item.current_assets is not None:
        current_assets = latest_item.current_assets
    
    if hasattr(latest_item, 'current_liabilities') and latest_item.current_liabilities is not None:
        current_liabilities = latest_item.current_liabilities
        
    current_ratio = None
    if current_assets and current_liabilities:
        current_ratio = current_assets / current_liabilities
        if current_ratio >= 2:
            score += 2
            details.append(f"Strong current ratio: {current_ratio:.2f}")
        elif current_ratio >= 1.5:
            score += 1
            details.append(f"Acceptable current ratio: {current_ratio:.2f}")
        else:
            details.append(f"Weak current ratio: {current_ratio:.2f}")
    else:
        details.append("Current ratio could not be calculated (missing data)")

    # 2. 债务与资产比率 - Debt vs. Assets
    if hasattr(latest_item, 'total_assets') and latest_item.total_assets is not None:
        total_assets = latest_item.total_assets
    else:
        details.append("Cannot compute debt ratio (missing total_assets).")
        return {"score": score, "details": "; ".join(details)}

    if hasattr(latest_item, 'total_liabilities') and latest_item.total_liabilities is not None:
        total_liabilities = latest_item.total_liabilities
    else:
        details.append("Cannot compute debt ratio (missing total_liabilities).")
        return {"score": score, "details": "; ".join(details)}

    if total_assets > 0:
        debt_ratio = total_liabilities / total_assets
        if debt_ratio < 0.5:
            score += 2
            details.append(f"Debt ratio = {debt_ratio:.2f}, under 0.50 (conservative).")
        elif debt_ratio < 0.8:
            score += 1
            details.append(f"Debt ratio = {debt_ratio:.2f}, somewhat high but could be acceptable.")
        else:
            details.append(f"Debt ratio = {debt_ratio:.2f}, quite high by Graham standards.")
    else:
        details.append("Cannot compute debt ratio (missing total_assets).")

    # 3. 分红记录 - Dividend track record
    div_periods = [item.dividends_and_other_cash_distributions for item in financial_line_items if item.dividends_and_other_cash_distributions is not None]
    if div_periods:
        # In many data feeds, dividend outflow is shown as a negative number
        # (money going out to shareholders). We'll consider any negative as 'paid a dividend'.
        div_paid_years = sum(1 for d in div_periods if d < 0)
        if div_paid_years > 0:
            # e.g. if at least half the periods had dividends
            if div_paid_years >= (len(div_periods) // 2 + 1):
                score += 1
                details.append("Company paid dividends in the majority of the reported years.")
            else:
                details.append("Company has some dividend payments, but not most years.")
        else:
            details.append("Company did not pay dividends in these periods.")
    else:
        details.append("No dividend data available to assess payout consistency.")

    return {"score": score, "details": "; ".join(details)}


def analyze_valuation_graham(metrics: list, financial_line_items: list, market_cap: float) -> dict:
    """
    分析格雷厄姆式估值
    格雷厄姆偏好：
    1. Net-Nets：净流动资产价值 > 市值
    2. 低市净率配合合理的收益率
    3. 格雷厄姆数字与当前价格对比
    
    Graham valuation analysis
    Graham favors:
    1. Net-Nets: NCAV > Market Cap.
    2. Low P/B with decent earnings yield.
    3. Graham Number vs current price.
    """
    if not financial_line_items or market_cap is None:
        return {"score": 0, "details": "Insufficient data for Graham valuation"}

    latest = financial_line_items[0]
    
    # 添加适当的属性检查 - Add proper attribute checks for all attributes
    current_assets = 0
    if hasattr(latest, 'current_assets') and latest.current_assets is not None:
        current_assets = latest.current_assets
        
    total_liabilities = 0
    if hasattr(latest, 'total_liabilities') and latest.total_liabilities is not None:
        total_liabilities = latest.total_liabilities
        
    book_value_ps = 0
    if hasattr(latest, 'book_value_per_share') and latest.book_value_per_share is not None:
        book_value_ps = latest.book_value_per_share
        
    eps = 0
    if hasattr(latest, 'earnings_per_share') and latest.earnings_per_share is not None:
        eps = latest.earnings_per_share
        
    shares_outstanding = 0
    if hasattr(latest, 'outstanding_shares') and latest.outstanding_shares is not None:
        shares_outstanding = latest.outstanding_shares

    details = []
    score = 0

    # 1. Net-Net检查 - Net-Net Check
    #   NCAV = Current Assets - Total Liabilities
    #   If NCAV > Market Cap => historically a strong buy signal
    net_current_asset_value = current_assets - total_liabilities
    if net_current_asset_value > 0 and shares_outstanding > 0:
        net_current_asset_value_per_share = net_current_asset_value / shares_outstanding
        price_per_share = market_cap / shares_outstanding if shares_outstanding else 0

        details.append(f"Net Current Asset Value = {net_current_asset_value:,.2f}")
        details.append(f"NCAV Per Share = {net_current_asset_value_per_share:,.2f}")
        details.append(f"Price Per Share = {price_per_share:,.2f}")

        if net_current_asset_value > market_cap:
            score += 4  # 非常强的格雷厄姆信号 - Very strong Graham signal
            details.append("Net-Net: NCAV > Market Cap (classic Graham deep value).")
        else:
            # 部分净净价值折扣 - For partial net-net discount
            if net_current_asset_value_per_share >= (price_per_share * 0.67):
                score += 2
                details.append("NCAV Per Share >= 2/3 of Price Per Share (moderate net-net discount).")
    else:
        details.append("NCAV not exceeding market cap or insufficient data for net-net approach.")

    # 2. 格雷厄姆数字 - Graham Number
    #   GrahamNumber = sqrt(22.5 * EPS * BVPS).
    #   Compare the result to the current price_per_share
    #   If GrahamNumber >> price, indicates undervaluation
    graham_number = None
    if eps > 0 and book_value_ps > 0:
        graham_number = math.sqrt(22.5 * eps * book_value_ps)
        details.append(f"Graham Number = {graham_number:.2f}")
    else:
        details.append("Unable to compute Graham Number (EPS or Book Value missing/<=0).")

    # 3. 相对于格雷厄姆数字的安全边际 - Margin of Safety relative to Graham Number
    if graham_number and shares_outstanding > 0:
        current_price = market_cap / shares_outstanding
        if current_price > 0:
            margin_of_safety = (graham_number - current_price) / current_price
            details.append(f"Margin of Safety (Graham Number) = {margin_of_safety:.2%}")
            if margin_of_safety > 0.5:
                score += 3
                details.append("Price is well below Graham Number (>=50% margin).")
            elif margin_of_safety > 0.2:
                score += 1
                details.append("Some margin of safety relative to Graham Number.")
            else:
                details.append("Price close to or above Graham Number, low margin of safety.")
        else:
            details.append("Current price is zero or invalid; can't compute margin of safety.")
    # else: already appended details for missing graham_number

    return {"score": score, "details": "; ".join(details)}


# 移除了 model_name 和 model_provider 参数，因为模型固定为 GPT-4o
# Removed model_name and model_provider parameters as the model is fixed to GPT-4o
def generate_graham_output(
    ticker: str,
    analysis_data: dict[str, any],
) -> BenGrahamSignal:
    """
    生成本杰明·格雷厄姆风格的投资决策：
    - 强调价值、安全边际、净净值、保守的资产负债表、稳定的收益。
    - 以JSON结构返回结果：{ signal, confidence, reasoning }。
    
    Generates an investment decision in the style of Benjamin Graham:
    - Value emphasis, margin of safety, net-nets, conservative balance sheet, stable earnings.
    - Return the result in a JSON structure: { signal, confidence, reasoning }.
    """

    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是一个基于本杰明·格雷厄姆原则的AI投资代理，做出投资决策时遵循以下原则：
            1. 通过购买低于内在价值的股票（如格雷厄姆数、净流动资产价值）确保安全边际。
            2. 强调公司的财务实力（低杠杆、充足的流动资产）。
            3. 偏好多年稳定盈利。
            4. 考虑分红记录以增加安全性。
            5. 避免投机或高增长假设；专注于已验证的指标。
            
            在提供推理时，需全面且具体：
            1. 解释影响决策的关键估值指标（格雷厄姆数、NCAV、P/E等）。
            2. 突出具体的财务实力指标（流动比率、债务水平等）。
            3. 引用盈利的稳定性或不稳定性。
            4. 提供精确的定量证据。
            5. 将当前指标与格雷厄姆的特定阈值比较（如"流动比率2.5超过格雷厄姆的最低要求2.0"）。
            6. 使用本杰明·格雷厄姆保守、分析性的语气和风格。
            
            例如，看涨信号："该股票以净流动资产价值35%的折扣交易，提供了充足的安全边际。流动比率2.5和债务权益比0.3表明财务状况强劲..."
            例如，看跌信号："尽管盈利稳定，但当前价格50美元超过了我们计算的格雷厄姆数35美元，没有安全边际。此外，流动比率仅为1.2低于格雷厄姆偏好的2.0阈值..."
                        
            返回一个理性的推荐：买入、卖出或中性，附带置信度（0-100）和详细的推理。
            """
        ),
        (
            "human",
            """根据以下分析，创建一个格雷厄姆式的投资信号：

            股票{ticker} 的分析数据:
            {analysis_data}

            按照此格式返回 JSON:
            {{
              "signal": "买入/中性/卖出",
              "confidence": float (0-100),
              "reasoning": "string"
            }}
            """
        )
    ])

    prompt = template.invoke({
        "analysis_data": json.dumps(analysis_data, indent=2),
        "ticker": ticker
    })

    def create_default_ben_graham_signal():
        """创建默认的Ben Graham信号 - Create default Ben Graham signal"""
        return BenGrahamSignal(signal="中性", confidence=0.0, reasoning="Error in generating analysis; defaulting to neutral.")

    # 调用 call_llm 时不再传递 model_name 和 model_provider
    # model_name and model_provider are no longer passed when calling call_llm
    return call_llm(
        prompt=prompt,
        pydantic_model=BenGrahamSignal,
        agent_name="ben_graham_agent",
        default_factory=create_default_ben_graham_signal,
    )
