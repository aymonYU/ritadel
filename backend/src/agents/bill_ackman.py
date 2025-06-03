"""
Bill Ackman激进投资分析师代理 - 基于比尔·阿克曼的积极投资策略
Bill Ackman activist investor analyst agent - Based on Bill Ackman's activist investment strategies
"""
from graph.state import AgentState, show_agent_reasoning
from tools.api import get_financial_metrics, get_market_cap, search_line_items
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm


class BillAckmanSignal(BaseModel):
    """
    Bill Ackman分析信号模型 - 包含投资信号、置信度和推理
    Bill Ackman analysis signal model - Contains investment signal, confidence and reasoning

    该模型用于表示基于阿克曼投资原则的交易信号结果
    This model represents trading signal results based on Ackman's investment principles

    Attributes:
        signal: 交易信号，可以是买入、卖出或中性 / Trading signal: buy, sell or neutral
        confidence: 信号的置信度，范围0-100 / Signal confidence, range 0-100
        reasoning: 产生该信号的详细理由说明 / Detailed reasoning for the signal
    """
    signal: Literal["买入", "卖出", "中性"]
    confidence: float
    reasoning: str


def bill_ackman_agent(state: AgentState):
    """
    使用比尔·阿克曼的投资原则和LLM推理分析股票
    获取多个时期的数据以便分析长期趋势
    阿克曼的核心投资策略：
    1. 寻找被低估的高质量企业
    2. 专注于具有强大竞争优势的公司
    3. 通过积极投资推动企业价值实现
    4. 重视管理层质量和资本配置能力
    5. 长期持有集中投资组合
    
    Analyzes stocks using Bill Ackman's investing principles and LLM reasoning.
    Fetches multiple periods of data so we can analyze long-term trends.
    Ackman's core investment strategy:
    1. Look for undervalued, high-quality businesses
    2. Focus on companies with strong competitive advantages
    3. Drive value realization through activist investing
    4. Value management quality and capital allocation
    5. Hold concentrated portfolio for long term
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    
    # 收集分析数据 - Collect analysis data
    analysis_data = {}
    ackman_analysis = {}
    
    for ticker in tickers:
        progress.update_status("bill_ackman_agent", ticker, "Fetching financial metrics")
        # 可以调整这些参数（period="annual"/"ttm", limit=5/10等）
        # You can adjust these parameters (period="annual"/"ttm", limit=5/10, etc.)
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=5)
        
        progress.update_status("bill_ackman_agent", ticker, "Gathering financial line items")
        # 请求多个时期的数据（年度或TTM）以获得更强健的长期视图
        # Request multiple periods of data (annual or TTM) for a more robust long-term view.
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",  # 收入
                "operating_margin",  # 营业利润率
                "debt_to_equity",  # 债务股权比
                "free_cash_flow",  # 自由现金流
                "total_assets",  # 总资产
                "total_liabilities",  # 总负债
                "dividends_and_other_cash_distributions",  # 分红和其他现金分配
                "outstanding_shares"  # 流通股数
            ],
            end_date,
            period="annual",  # 或"ttm"如果偏好过去12个月 - or "ttm" if you prefer trailing 12 months
            limit=5           # 获取多达5个年度周期（如需要可更多）- fetch up to 5 annual periods (or more if needed)
        )
        
        progress.update_status("bill_ackman_agent", ticker, "Getting market cap")
        market_cap = get_market_cap(ticker, end_date)
        
        progress.update_status("bill_ackman_agent", ticker, "Analyzing business quality")
        # 分析业务质量 - Analyze business quality
        quality_analysis = analyze_business_quality(metrics, financial_line_items)
        
        progress.update_status("bill_ackman_agent", ticker, "Analyzing balance sheet and capital structure")
        # 分析资产负债表和资本结构 - Analyze balance sheet and capital structure
        balance_sheet_analysis = analyze_financial_discipline(metrics, financial_line_items)
        
        progress.update_status("bill_ackman_agent", ticker, "Calculating intrinsic value & margin of safety")
        # 计算内在价值和安全边际 - Calculate intrinsic value & margin of safety
        valuation_analysis = analyze_valuation(financial_line_items, market_cap)
        
        # 合并部分评分或信号 - Combine partial scores or signals
        total_score = quality_analysis["score"] + balance_sheet_analysis["score"] + valuation_analysis["score"]
        max_possible_score = 15  # 根据需要调整权重 - Adjust weighting as desired
        
        # 生成简单的买入/持有/卖出（买入/中性/卖出）信号
        # Generate a simple buy/hold/sell (buy/neutral/sell) signal
        if total_score >= 0.7 * max_possible_score:
            signal = "买入"
        elif total_score <= 0.3 * max_possible_score:
            signal = "卖出"
        else:
            signal = "中性"
        
        # 整合所有分析数据 - Combine all analysis data
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "quality_analysis": quality_analysis,
            "balance_sheet_analysis": balance_sheet_analysis,
            "valuation_analysis": valuation_analysis
        }
        
        progress.update_status("bill_ackman_agent", ticker, "Generating Ackman analysis")
        ackman_output = generate_ackman_output(
            ticker=ticker, 
            analysis_data=analysis_data,
        )
        
        ackman_analysis[ticker] = {
            "signal": ackman_output.signal,
            "confidence": ackman_output.confidence,
            "reasoning": ackman_output.reasoning
        }
        
        progress.update_status("bill_ackman_agent", ticker, "Done")
    
    # 将结果包装在单个消息中以供链式传递 - Wrap results in a single message for the chain
    message = HumanMessage(
        content=json.dumps(ackman_analysis),
        name="bill_ackman_agent"
    )
    
    # 如果请求，显示推理过程 - Show reasoning if requested
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(ackman_analysis, "Bill Ackman Agent")
    
    # 将信号添加到整体状态 - Add signals to the overall state
    state["data"]["analyst_signals"]["bill_ackman_agent"] = ackman_analysis

    return {
        "messages": [message],
        "data": state["data"]
    }


def analyze_business_quality(metrics: list, financial_line_items: list) -> dict:
    """
    分析公司是否具有高质量的业务，具备稳定或增长的现金流，
    持久的竞争优势，以及长期增长的潜力
    阿克曼特别关注：
    - 强劲的收入增长轨迹
    - 持续的高运营利润率
    - 稳定的自由现金流生成
    - 高股本回报率表明存在护城河
    
    Analyze whether the company has a high-quality business with stable or growing cash flows,
    durable competitive advantages, and potential for long-term growth.
    Ackman particularly focuses on:
    - Strong revenue growth trajectory
    - Consistent high operating margins
    - Stable free cash flow generation
    - High ROE indicating moat presence
    """
    score = 0
    details = []
    
    if not metrics or not financial_line_items:
        return {
            "score": 0,
            "details": "业务质量分析数据不足。"
        }
    
    # 1. 多期收入增长分析 - Multi-period revenue growth analysis
    revenues = [getattr(item, 'revenue', None) for item in financial_line_items if getattr(item, 'revenue', None) is not None]
    if len(revenues) >= 2:
        # 检查收入从第一期到最后一期是否整体增长 - Check if overall revenue grew from first to last
        initial, final = revenues[0], revenues[-1]
        if initial and final and final > initial:
            # 简单增长率 - Simple growth rate
            growth_rate = (final - initial) / abs(initial)
            if growth_rate > 0.5:  # 例如，在可用时间内增长50% - e.g., 50% growth over the available time
                score += 2
                details.append(f"收入在整个期间增长了{(growth_rate*100):.1f}%。")
            else:
                score += 1
                details.append(f"收入增长为正但累计低于50%（{(growth_rate*100):.1f}%）。")
        else:
            details.append("收入没有显著增长或数据不足。")
    else:
        details.append("多期趋势的收入数据不足。")
    
    # 2. 营业利润率和自由现金流一致性 - Operating margin and free cash flow consistency
    # 检查营业利润率或自由现金流是否持续为正/改善
    # We'll check if operating_margin or free_cash_flow are consistently positive/improving
    fcf_vals = [getattr(item, 'free_cash_flow', None) for item in financial_line_items if getattr(item, 'free_cash_flow', None) is not None]
    op_margin_vals = [getattr(item, 'operating_margin', None) for item in financial_line_items if getattr(item, 'operating_margin', None) is not None]
    
    if op_margin_vals:
        # 检查大部分营业利润率是否>15% - Check if the majority of operating margins are > 15%
        above_15 = sum(1 for m in op_margin_vals if m > 0.15)
        if above_15 >= (len(op_margin_vals) // 2 + 1):
            score += 2
            details.append("营业利润率经常超过15%。")
        else:
            details.append("营业利润率未持续保持在15%以上。")
    else:
        details.append("各期间无营业利润率数据。")
    
    if fcf_vals:
        # 检查自由现金流在大部分时期是否为正 - Check if free cash flow is positive in most periods
        positive_fcf_count = sum(1 for f in fcf_vals if f > 0)
        if positive_fcf_count >= (len(fcf_vals) // 2 + 1):
            score += 1
            details.append("大部分期间显示正自由现金流。")
        else:
            details.append("自由现金流未持续为正。")
    else:
        details.append("各期间无自由现金流数据。")
    
    # 3. 最新指标的股本回报率(ROE)检查 - Return on Equity (ROE) check from the latest metrics
    # （如果需要多期ROE，也需要在financial_line_items中包含）
    # (If you want multi-period ROE, you'd need that in financial_line_items as well.)
    latest_metrics = metrics[0]
    roe = getattr(latest_metrics, 'return_on_equity', None)
    if roe and roe > 0.15:
        score += 2
        details.append(f"高ROE为{roe:.1%}，表明潜在护城河。")
    elif roe:
        details.append(f"ROE为{roe:.1%}，不表明强护城河。")
    else:
        details.append("指标中无ROE数据。")
    
    return {
        "score": score,
        "details": "; ".join(details)
    }


def analyze_financial_discipline(metrics: list, financial_line_items: list) -> dict:
    """
    评估公司在多个期间的资产负债表：
    - 债务比率趋势
    - 长期向股东返还资本（股息、回购）
    
    Evaluate the company's balance sheet over multiple periods:
    - Debt ratio trends
    - Capital returns to shareholders over time (dividends, buybacks)
    """
    score = 0
    details = []
    
    if not metrics or not financial_line_items:
        return {
            "score": 0,
            "details": "财务纪律分析数据不足。"
        }
    
    # 1. Multi-period debt ratio or debt_to_equity
    # Check if the company's leverage is stable or improving
    debt_to_equity_vals = [getattr(item, 'debt_to_equity', None) for item in financial_line_items 
                          if getattr(item, 'debt_to_equity', None) is not None]
    
    # If we have multi-year data, see if D/E ratio has gone down or stayed <1 across most periods
    if debt_to_equity_vals:
        below_one_count = sum(1 for d in debt_to_equity_vals if d < 1.0)
        if below_one_count >= (len(debt_to_equity_vals) // 2 + 1):
            score += 2
            details.append("大部分期间债务权益比<1.0。")
        else:
            details.append("许多期间债务权益比≥1.0。")
    else:
        # Fallback to total_liabilities/total_assets if D/E not available
        liab_to_assets = []
        for item in financial_line_items:
            total_liabilities = getattr(item, 'total_liabilities', None)
            total_assets = getattr(item, 'total_assets', None)
            if total_liabilities and total_assets and total_assets > 0:
                liab_to_assets.append(total_liabilities / total_assets)
        
        if liab_to_assets:
            below_50pct_count = sum(1 for ratio in liab_to_assets if ratio < 0.5)
            if below_50pct_count >= (len(liab_to_assets) // 2 + 1):
                score += 2
                details.append("大部分期间负债资产比<50%。")
            else:
                details.append("许多期间负债资产比≥50%。")
        else:
            details.append("无一致的杠杆比率数据。")
    
    # 2. Capital allocation approach (dividends + share counts)
    # If the company paid dividends or reduced share count over time, it may reflect discipline
    dividends_list = [getattr(item, 'dividends_and_other_cash_distributions', None) for item in financial_line_items if getattr(item, 'dividends_and_other_cash_distributions', None) is not None]
    if dividends_list:
        # Check if dividends were paid (i.e., negative outflows to shareholders) in most periods
        paying_dividends_count = sum(1 for d in dividends_list if d < 0)
        if paying_dividends_count >= (len(dividends_list) // 2 + 1):
            score += 1
            details.append("公司有向股东返还资本的历史（股息）。")
        else:
            details.append("股息未持续支付或无数据。")
    else:
        details.append("各期间无股息数据。")
    
    # Check for decreasing share count (simple approach):
    # We can compare first vs last if we have at least two data points
    shares = [getattr(item, 'outstanding_shares', None) for item in financial_line_items if getattr(item, 'outstanding_shares', None) is not None]
    if len(shares) >= 2:
        if shares[-1] < shares[0]:
            score += 1
            details.append("流通股数随时间减少（可能回购）。")
        else:
            details.append("流通股数在可用期间内未减少。")
    else:
        details.append("无多期股数数据来评估回购。")
    
    return {
        "score": score,
        "details": "; ".join(details)
    }


def analyze_valuation(financial_line_items: list, market_cap: float) -> dict:
    """
    阿克曼投资于以内在价值折价交易的公司。
    我们可以做简化的DCF或基于FCF的方法。
    此函数目前仅使用最新的自由现金流，
    但可以扩展为使用平均或多年FCF方法。
    
    Ackman invests in companies trading at a discount to intrinsic value.
    We can do a simplified DCF or an FCF-based approach.
    This function currently uses the latest free cash flow only, 
    but you could expand it to use an average or multi-year FCF approach.
    """
    if not financial_line_items or market_cap is None:
        return {
            "score": 0,
            "details": "估值数据不足。"
        }
    
    # Example: use the most recent item for FCF
    latest = financial_line_items[-1]  # the last one is presumably the most recent
    fcf = getattr(latest, 'free_cash_flow', None) or 0
    
    # For demonstration, let's do a naive approach:
    growth_rate = 0.06
    discount_rate = 0.10
    terminal_multiple = 15
    projection_years = 5
    
    if fcf <= 0:
        return {
            "score": 0,
            "details": f"无正FCF进行估值；FCF = {fcf}。",
            "intrinsic_value": None
        }
    
    present_value = 0
    for year in range(1, projection_years + 1):
        future_fcf = fcf * (1 + growth_rate) ** year
        pv = future_fcf / ((1 + discount_rate) ** year)
        present_value += pv
    
    # Terminal Value
    terminal_value = (fcf * (1 + growth_rate) ** projection_years * terminal_multiple) \
                     / ((1 + discount_rate) ** projection_years)
    intrinsic_value = present_value + terminal_value
    
    # Compare with market cap => margin of safety
    margin_of_safety = (intrinsic_value - market_cap) / market_cap
    
    score = 0
    if margin_of_safety > 0.3:
        score += 3
    elif margin_of_safety > 0.1:
        score += 1
    
    details = [
        f"计算内在价值：~{intrinsic_value:,.2f} / Calculated intrinsic value: ~{intrinsic_value:,.2f}",
        f"市值：~{market_cap:,.2f} / Market cap: ~{market_cap:,.2f}",
        f"安全边际：{margin_of_safety:.2%} / Margin of safety: {margin_of_safety:.2%}"
    ]
    
    return {
        "score": score,
        "details": "; ".join(details),
        "intrinsic_value": intrinsic_value,
        "margin_of_safety": margin_of_safety
    }


def generate_ackman_output(
    ticker: str,
    analysis_data: dict[str, any],
) -> BillAckmanSignal:
    """
    基于比尔·阿克曼的风格生成投资决策
    Generates investment decisions in the style of Bill Ackman.
    """
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是比尔·阿克曼的人工智能代理，使用他的原则做出投资决策：

            1. 寻找具有持久竞争优势（护城河）的高质量企业。
            2. 优先考虑持续的自由现金流和增长潜力。
            3. 倡导强有力的财务纪律（合理杠杆、高效资本配置）。
            4. 估值很重要：目标内在价值和安全边际。
            5. 对集中投资组合进行高信念的长期投资。
            6. 如果管理层或运营改进能够释放价值，采取积极投资方法。
            
            规则：
            - 评估品牌实力、市场地位或其他护城河。
            - 检查自由现金流生成、稳定或增长的收益。
            - 分析资产负债表健康状况（合理债务、良好ROE）。
            - 以内在价值折价买入；折价越高 => 信念越强。
            - 如果管理层不佳或有战略改进路径，积极参与。
            - 提供理性、数据驱动的建议（买入、卖出或中性）。

            严格按照以下JSON格式返回交易信号：
            {{
              "signal": "买入" | "卖出" | "中性",
              "confidence": 0到100之间的浮点数,
              "reasoning": "字符串"
            }}"""
        ),
        (
            "human",
            """基于以下分析，创建阿克曼风格的投资信号。

            {ticker}的分析数据：
            {analysis_data}

            完全按照以下JSON格式返回交易信号：
            {{
              "signal": "买入" | "卖出" | "中性",
              "confidence": 0到100之间的浮点数,
              "reasoning": "字符串"
            }}
            """
        )
    ])

    prompt = template.invoke({
        "analysis_data": json.dumps(analysis_data, indent=2),
        "ticker": ticker
    })

    def create_default_bill_ackman_signal():
        return BillAckmanSignal(
            signal="中性",
            confidence=0.0,
            reasoning="分析错误，默认为中性。"
        )

    return call_llm(
        prompt=prompt, 
        pydantic_model=BillAckmanSignal, 
        agent_name="bill_ackman_agent", 
        default_factory=create_default_bill_ackman_signal,
    )
