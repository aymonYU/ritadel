"""
估值分析代理 - 多方法估值分析系统
Valuation Analysis Agent - Multi-methodology valuation analysis system

实现DCF估值、巴菲特业主盈利法等多种估值方法
Implements DCF valuation, Buffett's Owner Earnings method and other valuation methodologies
"""
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json

from tools.api import get_financial_metrics, get_market_cap, search_line_items


##### 估值代理 - Valuation Agent #####
def valuation_agent(state: AgentState):
    """
    对多个股票代码执行详细的估值分析，使用多种估值方法：
    1. DCF现金流折现模型
    2. 巴菲特业主盈利法
    3. 相对估值分析
    4. 安全边际计算
    
    Performs detailed valuation analysis using multiple methodologies for multiple tickers:
    1. DCF (Discounted Cash Flow) model
    2. Buffett's Owner Earnings method
    3. Relative valuation analysis
    4. Margin of safety calculation
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    # 为每个股票代码初始化估值分析 - Initialize valuation analysis for each ticker
    valuation_analysis = {}

    for ticker in tickers:
        progress.update_status("valuation_agent", ticker, "Fetching financial data")

        # 获取财务指标 - Fetch the financial metrics
        financial_metrics = get_financial_metrics(
            ticker=ticker,
            end_date=end_date,
            period="ttm",
        )

        # 财务指标安全检查 - Add safety check for financial metrics
        if not financial_metrics:
            progress.update_status("valuation_agent", ticker, "Failed: No financial metrics found")
            continue
        
        metrics = financial_metrics[0]

        progress.update_status("valuation_agent", ticker, "Gathering line items")
        # 获取估值所需的特定财务科目 - Fetch the specific line_items that we need for valuation purposes
        financial_line_items = search_line_items(
            ticker=ticker,
            line_items=[
                "free_cash_flow",  # 自由现金流
                "net_income",  # 净利润
                "depreciation_and_amortization",  # 折旧摊销
                "capital_expenditure",  # 资本支出
                "working_capital",  # 营运资本
            ],
            end_date=end_date,
            period="ttm",
            limit=2,
        )

        # 财务科目安全检查 - Add safety check for financial line items
        if len(financial_line_items) < 2:
            progress.update_status("valuation_agent", ticker, "Failed: Insufficient financial line items")
            continue

        # 获取当前和上期财务科目数据 - Pull the current and previous financial line items
        current_financial_line_item = financial_line_items[0]
        previous_financial_line_item = financial_line_items[1]

        progress.update_status("valuation_agent", ticker, "Calculating owner earnings")
        # 安全检查营运资本属性 - Safely check for working_capital attribute
        if (hasattr(current_financial_line_item, 'working_capital') and 
            hasattr(previous_financial_line_item, 'working_capital') and
            current_financial_line_item.working_capital is not None and 
            previous_financial_line_item.working_capital is not None):
            
            working_capital_change = current_financial_line_item.working_capital - previous_financial_line_item.working_capital
        else:
            # 如果营运资本数据不可用则默认为零 - Default to zero if working_capital attribute is not available
            working_capital_change = 0
            progress.update_status("valuation_agent", ticker, "Note: Working capital data not available")

        # 业主盈利估值（巴菲特方法）- Owner Earnings Valuation (Buffett Method)
        owner_earnings_value = calculate_owner_earnings_value(
            net_income=current_financial_line_item.net_income,
            depreciation=current_financial_line_item.depreciation_and_amortization,
            capex=current_financial_line_item.capital_expenditure,
            working_capital_change=working_capital_change,
            growth_rate=metrics.earnings_growth,
            required_return=0.15,  # 要求回报率15% - Required return 15%
            margin_of_safety=0.25,  # 安全边际25% - Margin of safety 25%
        )

        progress.update_status("valuation_agent", ticker, "Calculating DCF value")
        # DCF估值 - DCF Valuation
        dcf_value = calculate_intrinsic_value(
            free_cash_flow=current_financial_line_item.free_cash_flow,
            growth_rate=metrics.earnings_growth,
            discount_rate=0.10,  # 折现率10% - Discount rate 10%
            terminal_growth_rate=0.03,  # 永续增长率3% - Terminal growth rate 3%
            num_years=5,  # 预测5年 - 5-year projection
        )

        progress.update_status("valuation_agent", ticker, "Comparing to market value")
        # 获取市值 - Get the market cap
        market_cap = get_market_cap(ticker=ticker, end_date=end_date)

        # 计算综合估值差距（两种方法的平均值）- Calculate combined valuation gap (average of both methods)
        dcf_gap = (dcf_value - market_cap) / market_cap
        owner_earnings_gap = (owner_earnings_value - market_cap) / market_cap
        valuation_gap = (dcf_gap + owner_earnings_gap) / 2

        # 生成交易信号 - Generate trading signal
        if valuation_gap > 0.15:  # 超过15%低估 - More than 15% undervalued
            signal = "bullish"
        elif valuation_gap < -0.15:  # 超过15%高估 - More than 15% overvalued
            signal = "bearish"
        else:
            signal = "neutral"

        # 创建推理依据 - Create the reasoning
        reasoning = {}
        reasoning["dcf_analysis"] = {
            "signal": ("bullish" if dcf_gap > 0.15 else "bearish" if dcf_gap < -0.15 else "neutral"),
            "details": f"内在价值: ${dcf_value:,.2f}, 市值: ${market_cap:,.2f}, 差距: {dcf_gap:.1%} - Intrinsic Value: ${dcf_value:,.2f}, Market Cap: ${market_cap:,.2f}, Gap: {dcf_gap:.1%}",
        }

        reasoning["owner_earnings_analysis"] = {
            "signal": ("bullish" if owner_earnings_gap > 0.15 else "bearish" if owner_earnings_gap < -0.15 else "neutral"),
            "details": f"业主盈利价值: ${owner_earnings_value:,.2f}, 市值: ${market_cap:,.2f}, 差距: {owner_earnings_gap:.1%} - Owner Earnings Value: ${owner_earnings_value:,.2f}, Market Cap: ${market_cap:,.2f}, Gap: {owner_earnings_gap:.1%}",
        }

        confidence = round(abs(valuation_gap), 2) * 100
        valuation_analysis[ticker] = {
            "signal": signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status("valuation_agent", ticker, "Done")

    # 创建消息 - Create message
    message = HumanMessage(
        content=json.dumps(valuation_analysis),
        name="valuation_agent",
    )

    # 如果设置了标志则打印推理过程 - Print the reasoning if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(valuation_analysis, "Valuation Analysis Agent")

    # 将信号添加到analyst_signals列表 - Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["valuation_agent"] = valuation_analysis

    return {
        "messages": [message],
        "data": data,
    }


def calculate_owner_earnings_value(
    net_income: float,
    depreciation: float,
    capex: float,
    working_capital_change: float,
    growth_rate: float = 0.05,
    required_return: float = 0.15,
    margin_of_safety: float = 0.25,
    num_years: int = 5,
) -> float:
    """
    使用巴菲特的业主盈利法计算内在价值
    
    业主盈利 = 净利润 + 折旧摊销 - 资本支出 - 营运资本变化
    
    这是巴菲特用来评估企业真实盈利能力的关键指标，
    反映了股东可以从企业中实际获得的现金流。
    
    Calculates the intrinsic value using Buffett's Owner Earnings method.

    Owner Earnings = Net Income + Depreciation/Amortization - Capital Expenditures - Working Capital Changes
    
    This is the key metric Buffett uses to evaluate the true earning power of a business,
    representing the cash flow that shareholders can actually extract from the business.

    参数 Args:
        net_income: 年度净利润 - Annual net income
        depreciation: 年度折旧摊销 - Annual depreciation and amortization
        capex: 年度资本支出 - Annual capital expenditures
        working_capital_change: 年度营运资本变化 - Annual change in working capital
        growth_rate: 预期增长率 - Expected growth rate
        required_return: 要求回报率（巴菲特通常使用15%）- Required rate of return (Buffett typically uses 15%)
        margin_of_safety: 安全边际 - Margin of safety to apply to final value
        num_years: 预测年数 - Number of years to project

    返回 Returns:
        float: 包含安全边际的内在价值 - Intrinsic value with margin of safety
    """
    if not all([isinstance(x, (int, float)) for x in [net_income, depreciation, capex, working_capital_change]]):
        return 0

    # 计算初始业主盈利 - Calculate initial owner earnings
    owner_earnings = net_income + depreciation - capex - working_capital_change

    if owner_earnings <= 0:
        return 0
        
    # 确保增长率不为None - Ensure growth_rate is not None
    if growth_rate is None:
        growth_rate = 0.05  # 使用默认5%增长率 - Use a default 5% growth rate

    # 预测未来业主盈利 - Project future owner earnings
    future_values = []
    for year in range(1, num_years + 1):
        future_value = owner_earnings * (1 + growth_rate) ** year
        discounted_value = future_value / (1 + required_return) ** year
        future_values.append(discounted_value)

    # 计算终值（使用永续增长公式）- Calculate terminal value (using perpetuity growth formula)
    terminal_growth = min(growth_rate, 0.03)  # 终值增长率上限为3% - Cap terminal growth at 3%
    terminal_value = (future_values[-1] * (1 + terminal_growth)) / (required_return - terminal_growth)
    terminal_value_discounted = terminal_value / (1 + required_return) ** num_years

    # 汇总所有价值并应用安全边际 - Sum all values and apply margin of safety
    intrinsic_value = sum(future_values) + terminal_value_discounted
    value_with_safety_margin = intrinsic_value * (1 - margin_of_safety)

    return value_with_safety_margin


def calculate_intrinsic_value(
    free_cash_flow: float,
    growth_rate: float = 0.05,
    discount_rate: float = 0.10,
    terminal_growth_rate: float = 0.02,
    num_years: int = 5,
) -> float:
    """
    基于当前自由现金流计算公司的现金流折现（DCF）价值
    使用此函数计算股票的内在价值
    
    DCF模型是最广泛使用的估值方法之一，通过预测未来现金流
    并将其折现到现值来确定公司的内在价值
    
    Computes the discounted cash flow (DCF) for a given company based on the current free cash flow.
    Use this function to calculate the intrinsic value of a stock.
    
    DCF model is one of the most widely used valuation methods, determining the intrinsic value 
    of a company by projecting future cash flows and discounting them to present value.
    
    参数 Args:
        free_cash_flow: 当前自由现金流 - Current free cash flow
        growth_rate: 现金流增长率 - Cash flow growth rate
        discount_rate: 折现率（WACC或要求回报率）- Discount rate (WACC or required return)
        terminal_growth_rate: 终值增长率 - Terminal growth rate
        num_years: 预测年数 - Number of projection years
        
    返回 Returns:
        float: DCF内在价值 - DCF intrinsic value
    """
    # 检查自由现金流是否有效 - Check if free_cash_flow is valid
    if free_cash_flow is None or not isinstance(free_cash_flow, (int, float)):
        return 0
        
    # 确保增长率不为None - Ensure growth_rate is not None
    if growth_rate is None:
        growth_rate = 0.05  # 默认5%增长 - Default to 5% growth
        
    # 确保终值增长率不为None - Ensure terminal_growth_rate is not None
    if terminal_growth_rate is None:
        terminal_growth_rate = 0.02  # 默认2%终值增长 - Default to 2% terminal growth
        
    # 确保折现率不为None - Ensure discount_rate is not None
    if discount_rate is None:
        discount_rate = 0.10  # 默认10%折现率 - Default to 10% discount rate
    
    # 基于增长率估算未来现金流 - Estimate the future cash flows based on the growth rate
    cash_flows = [free_cash_flow * (1 + growth_rate) ** i for i in range(num_years)]

    # 计算预测现金流的现值 - Calculate the present value of projected cash flows
    present_values = []
    for i in range(num_years):
        present_value = cash_flows[i] / (1 + discount_rate) ** (i + 1)
        present_values.append(present_value)

    # 计算终值 - Calculate the terminal value
    terminal_value = cash_flows[-1] * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
    terminal_present_value = terminal_value / (1 + discount_rate) ** num_years

    # 汇总现值和终值 - Sum up the present values and terminal value
    dcf_value = sum(present_values) + terminal_present_value

    return dcf_value


def calculate_working_capital_change(
    current_working_capital: float,
    previous_working_capital: float,
) -> float:
    """
    计算两个期间之间营运资本的绝对变化
    
    营运资本变化是现金流分析的重要组成部分：
    - 正值变化意味着更多资本被占用在营运资本中（现金流出）
    - 负值变化意味着占用资本减少（现金流入）
    
    Calculate the absolute change in working capital between two periods.
    
    Working capital change is an important component of cash flow analysis:
    - A positive change means more capital is tied up in working capital (cash outflow)
    - A negative change means less capital is tied up (cash inflow)

    参数 Args:
        current_working_capital: 当前期间的营运资本 - Current period's working capital
        previous_working_capital: 上期营运资本 - Previous period's working capital

    返回 Returns:
        float: 营运资本变化（当前期间 - 上期）- Change in working capital (current - previous)
    """
    return current_working_capital - previous_working_capital
