from langchain_openai import ChatOpenAI
from graph.state import AgentState, show_agent_reasoning
from tools.api import get_financial_metrics, get_market_cap, search_line_items, get_insider_trades, get_company_news
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm

"""
Charlie Munger投资分析师代理 - 基于查理·芒格的投资原则和心理模型
Charlie Munger investing analyst agent - Based on Charlie Munger's investing principles and mental models
"""

class CharlieMungerSignal(BaseModel):
    """
    Charlie Munger分析信号模型 - 包含投资信号、置信度和推理
    Charlie Munger analysis signal model - Contains investment signal, confidence and reasoning
    """
    signal: Literal["买入", "卖出", "中性"]
    confidence: float
    reasoning: str


def charlie_munger_agent(state: AgentState):
    """
    使用查理·芒格的投资原则和心理模型分析股票
    专注于护城河强度、管理质量、可预测性和估值
    芒格的核心理念：
    1. 寻找具有强大护城河的优质企业
    2. 重视管理层的诚信和能力
    3. 偏好简单、可预测的商业模式
    4. 采用逆向思维和多学科方法
    5. 长期持有优质企业
    
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    
    # 收集分析数据 - Collect analysis data
    analysis_data = {}
    munger_analysis = {}
    
    for ticker in tickers:
        progress.update_status("charlie_munger_agent", ticker, "Fetching financial metrics")
        # 芒格关注长期数据 - Munger looks at longer periods
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=10)
        
        progress.update_status("charlie_munger_agent", ticker, "Gathering financial line items")
        # 获取芒格分析所需的关键财务指标 - Fetch key financial metrics for Munger's analysis
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",  # 收入
                "net_income",  # 净收入
                "operating_income",  # 营业收入
                "return_on_invested_capital",  # 投资资本回报率
                "gross_margin",  # 毛利率
                "operating_margin",  # 营业利润率
                "free_cash_flow",  # 自由现金流
                "capital_expenditure",  # 资本支出
                "cash_and_equivalents",  # 现金及等价物
                "total_debt",  # 总债务
                "shareholders_equity",  # 股东权益
                "outstanding_shares",  # 流通股数
                "research_and_development",  # 研发费用
                "goodwill_and_intangible_assets",  # 商誉和无形资产
            ],
            end_date,
            period="annual",
            limit=10  # 芒格重视长期趋势分析 - Munger examines long-term trends
        )
        
        progress.update_status("charlie_munger_agent", ticker, "Getting market cap")
        market_cap = get_market_cap(ticker, end_date)
        
        progress.update_status("charlie_munger_agent", ticker, "Fetching insider trades")
        # 芒格重视管理层的利益一致性 - Munger values management with skin in the game
        insider_trades = get_insider_trades(
            ticker,
            end_date,
            # 回溯2年查看内部交易模式 - Look back 2 years for insider trading patterns
            start_date=None,
            limit=100
        )
        
        progress.update_status("charlie_munger_agent", ticker, "Fetching company news")
        # 芒格避免负面新闻频繁的企业 - Munger avoids businesses with frequent negative press
        company_news = get_company_news(
            ticker,
            end_date,
            # 回溯1年查看新闻 - Look back 1 year for news
            start_date=None,
            limit=100
        )
        
        progress.update_status("charlie_munger_agent", ticker, "Analyzing moat strength")
        # 分析护城河强度 - Analyze moat strength
        moat_analysis = analyze_moat_strength(metrics, financial_line_items)
        
        progress.update_status("charlie_munger_agent", ticker, "Analyzing management quality")
        # 分析管理质量 - Analyze management quality
        management_analysis = analyze_management_quality(financial_line_items, insider_trades)
        
        progress.update_status("charlie_munger_agent", ticker, "Analyzing business predictability")
        # 分析业务可预测性 - Analyze business predictability
        predictability_analysis = analyze_predictability(financial_line_items)
        
        progress.update_status("charlie_munger_agent", ticker, "Calculating Munger-style valuation")
        # 计算芒格式估值 - Calculate Munger-style valuation
        valuation_analysis = calculate_munger_valuation(financial_line_items, market_cap)
        
        # 根据芒格的权重偏好合并评分 - Combine partial scores with Munger's weighting preferences
        # 芒格更重视质量和可预测性，而非当前估值 - Munger weights quality and predictability higher than current valuation
        total_score = (
            moat_analysis["score"] * 0.35 +  # 护城河权重35% - Moat weight 35%
            management_analysis["score"] * 0.25 +  # 管理层权重25% - Management weight 25%
            predictability_analysis["score"] * 0.25 +  # 可预测性权重25% - Predictability weight 25%
            valuation_analysis["score"] * 0.15  # 估值权重15% - Valuation weight 15%
        )
        
        max_possible_score = 10  # 标准化到0-10分 - Scale to 0-10
        
        # 生成买入/持有/卖出信号 - Generate a simple buy/hold/sell signal
        if total_score >= 7.5:  # 芒格的标准极高 - Munger has very high standards
            signal = "买入"
        elif total_score <= 4.5:
            signal = "卖出"
        else:
            signal = "中性"
        
        # 整合所有分析数据 - Combine all analysis data
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "moat_analysis": moat_analysis,
            "management_analysis": management_analysis,
            "predictability_analysis": predictability_analysis,
            "valuation_analysis": valuation_analysis,
            # 包含新闻定性评估 - Include some qualitative assessment from news
            "news_sentiment": analyze_news_sentiment(company_news) if company_news else "No news data available"
        }
        
        progress.update_status("charlie_munger_agent", ticker, "Generating Munger analysis")
        munger_output = generate_munger_output(
            ticker=ticker, 
            analysis_data=analysis_data,
        )
        
        munger_analysis[ticker] = {
            "signal": munger_output.signal,
            "confidence": munger_output.confidence,
            "reasoning": munger_output.reasoning
        }
        
        progress.update_status("charlie_munger_agent", ticker, "Done")
    
    # 将结果包装在单个消息中以供链式传递 - Wrap results in a single message for the chain
    message = HumanMessage(
        content=json.dumps(munger_analysis),
        name="charlie_munger_agent"
    )
    
    # 如果请求，显示推理过程 - Show reasoning if requested
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(munger_analysis, "Charlie Munger Agent")
    
    # 将信号添加到整体状态 - Add signals to the overall state
    state["data"]["analyst_signals"]["charlie_munger_agent"] = munger_analysis

    return {
        "messages": [message],
        "data": state["data"]
    }


def analyze_moat_strength(metrics: list, financial_line_items: list) -> dict:
    """
    使用芒格的方法分析企业的竞争优势：
    - 持续的高投资资本回报率(ROIC)
    - 定价权（稳定/改善的毛利率）
    - 低资本需求
    - 网络效应和无形资产（研发投资、商誉）
    
    Analyze the business's competitive advantage using Munger's approach:
    - Consistent high returns on capital (ROIC)
    - Pricing power (stable/improving gross margins)
    - Low capital requirements
    - Network effects and intangible assets (R&D investments, goodwill)
    """
    score = 0
    details = []
    
    if not metrics or not financial_line_items:
        return {
            "score": 0,
            "details": "Insufficient data to analyze moat strength"
        }
    
    # 1. 投资资本回报率(ROIC)分析 - 芒格最喜欢的指标
    # Return on Invested Capital (ROIC) analysis - Munger's favorite metric
    roic_values = [item.return_on_invested_capital for item in financial_line_items 
                   if hasattr(item, 'return_on_invested_capital') and item.return_on_invested_capital is not None]
    
    if roic_values:
        # 检查ROIC是否持续高于15%（芒格的阈值）- Check if ROIC consistently above 15% (Munger's threshold)
        high_roic_count = sum(1 for r in roic_values if r > 0.15)
        if high_roic_count >= len(roic_values) * 0.8:  # 80%的周期显示高ROIC - 80% of periods show high ROIC
            score += 3
            details.append(f"Excellent ROIC: >15% in {high_roic_count}/{len(roic_values)} periods")
        elif high_roic_count >= len(roic_values) * 0.5:  # 50%的周期 - 50% of periods
            score += 2
            details.append(f"Good ROIC: >15% in {high_roic_count}/{len(roic_values)} periods")
        elif high_roic_count > 0:
            score += 1
            details.append(f"Mixed ROIC: >15% in only {high_roic_count}/{len(roic_values)} periods")
        else:
            details.append("Poor ROIC: Never exceeds 15% threshold")
    else:
        details.append("No ROIC data available")
    
    # 2. 定价权 - 检查毛利率稳定性和趋势
    # Pricing power - check gross margin stability and trends
    gross_margins = [item.gross_margin for item in financial_line_items 
                    if hasattr(item, 'gross_margin') and item.gross_margin is not None]
    
    if gross_margins and len(gross_margins) >= 3:
        # Munger likes stable or improving gross margins
        margin_trend = sum(1 for i in range(1, len(gross_margins)) if gross_margins[i] >= gross_margins[i-1])
        if margin_trend >= len(gross_margins) * 0.7:  # Improving in 70% of periods
            score += 2
            details.append("Strong pricing power: Gross margins consistently improving")
        elif sum(gross_margins) / len(gross_margins) > 0.3:  # Average margin > 30%
            score += 1
            details.append(f"Good pricing power: Average gross margin {sum(gross_margins)/len(gross_margins):.1%}")
        else:
            details.append("Limited pricing power: Low or declining gross margins")
    else:
        details.append("Insufficient gross margin data")
    
    # 3. Capital intensity - Munger prefers low capex businesses
    if len(financial_line_items) >= 3:
        capex_to_revenue = []
        for item in financial_line_items:
            if (hasattr(item, 'capital_expenditure') and item.capital_expenditure is not None and 
                hasattr(item, 'revenue') and item.revenue is not None and item.revenue > 0):
                # Note: capital_expenditure is typically negative in financial statements
                capex_ratio = abs(item.capital_expenditure) / item.revenue
                capex_to_revenue.append(capex_ratio)
        
        if capex_to_revenue:
            avg_capex_ratio = sum(capex_to_revenue) / len(capex_to_revenue)
            if avg_capex_ratio < 0.05:  # Less than 5% of revenue
                score += 2
                details.append(f"Low capital requirements: Avg capex {avg_capex_ratio:.1%} of revenue")
            elif avg_capex_ratio < 0.10:  # Less than 10% of revenue
                score += 1
                details.append(f"Moderate capital requirements: Avg capex {avg_capex_ratio:.1%} of revenue")
            else:
                details.append(f"High capital requirements: Avg capex {avg_capex_ratio:.1%} of revenue")
        else:
            details.append("No capital expenditure data available")
    else:
        details.append("Insufficient data for capital intensity analysis")
    
    # 4. Intangible assets - Munger values R&D and intellectual property
    r_and_d = [item.research_and_development for item in financial_line_items
              if hasattr(item, 'research_and_development') and item.research_and_development is not None]
    
    goodwill_and_intangible_assets = [item.goodwill_and_intangible_assets for item in financial_line_items
               if hasattr(item, 'goodwill_and_intangible_assets') and item.goodwill_and_intangible_assets is not None]

    if r_and_d and len(r_and_d) > 0:
        if sum(r_and_d) > 0:  # If company is investing in R&D
            score += 1
            details.append("Invests in R&D, building intellectual property")
    
    if (goodwill_and_intangible_assets and len(goodwill_and_intangible_assets) > 0):
        score += 1
        details.append("Significant goodwill/intangible assets, suggesting brand value or IP")
    
    # Scale score to 0-10 range
    final_score = min(10, score * 10 / 9)  # Max possible raw score is 9
    
    return {
        "score": final_score,
        "details": "; ".join(details)
    }


def analyze_management_quality(financial_line_items: list, insider_trades: list) -> dict:
    """
    使用芒格的标准评估管理质量：
    - 资本配置智慧
    - 内部人员持股和交易
    - 现金管理效率
    - 坦诚和透明度
    - 长期专注
    
    Evaluate management quality using Munger's criteria:
    - Capital allocation wisdom
    - Insider ownership and transactions
    - Cash management efficiency
    - Candor and transparency
    - Long-term focus
    """
    score = 0
    details = []
    
    if not financial_line_items:
        return {
            "score": 0,
            "details": "Insufficient data to analyze management quality"
        }
    
    # 1. 资本配置 - 检查自由现金流与净收入比率
    # Capital allocation - Check FCF to net income ratio
    # 芒格重视将收益转化为现金的公司 - Munger values companies that convert earnings to cash
    fcf_values = [item.free_cash_flow for item in financial_line_items 
                 if hasattr(item, 'free_cash_flow') and item.free_cash_flow is not None]
    
    net_income_values = [item.net_income for item in financial_line_items 
                        if hasattr(item, 'net_income') and item.net_income is not None]
    
    if fcf_values and net_income_values and len(fcf_values) == len(net_income_values):
        # 计算每个周期的自由现金流与净收入比率 - Calculate FCF to Net Income ratio for each period
        fcf_to_ni_ratios = []
        for i in range(len(fcf_values)):
            if net_income_values[i] and net_income_values[i] > 0:
                fcf_to_ni_ratios.append(fcf_values[i] / net_income_values[i])
        
        if fcf_to_ni_ratios:
            avg_ratio = sum(fcf_to_ni_ratios) / len(fcf_to_ni_ratios)
            if avg_ratio > 1.1:  # 自由现金流 > 净收入表明良好的会计核算 - FCF > net income suggests good accounting
                score += 3
                details.append(f"Excellent cash conversion: FCF/NI ratio of {avg_ratio:.2f}")
            elif avg_ratio > 0.9:  # 自由现金流大致等于净收入 - FCF roughly equals net income
                score += 2
                details.append(f"Good cash conversion: FCF/NI ratio of {avg_ratio:.2f}")
            elif avg_ratio > 0.7:  # 自由现金流略低于净收入 - FCF somewhat lower than net income
                score += 1
                details.append(f"Moderate cash conversion: FCF/NI ratio of {avg_ratio:.2f}")
            else:
                details.append(f"Poor cash conversion: FCF/NI ratio of only {avg_ratio:.2f}")
        else:
            details.append("Could not calculate FCF to Net Income ratios")
    else:
        details.append("Missing FCF or Net Income data")
    
    # 2. 债务管理 - 芒格对债务谨慎 - Debt management - Munger is cautious about debt
    debt_values = [item.total_debt for item in financial_line_items 
                  if hasattr(item, 'total_debt') and item.total_debt is not None]
    
    equity_values = [item.shareholders_equity for item in financial_line_items 
                    if hasattr(item, 'shareholders_equity') and item.shareholders_equity is not None]
    
    if debt_values and equity_values and len(debt_values) == len(equity_values):
        # 计算最近期的债务股权比 - Calculate D/E ratio for most recent period
        recent_de_ratio = debt_values[0] / equity_values[0] if equity_values[0] > 0 else float('inf')
        
        if recent_de_ratio < 0.3:  # 极低债务 - Very low debt
            score += 3
            details.append(f"Conservative debt management: D/E ratio of {recent_de_ratio:.2f}")
        elif recent_de_ratio < 0.7:  # 适度债务 - Moderate debt
            score += 2
            details.append(f"Prudent debt management: D/E ratio of {recent_de_ratio:.2f}")
        elif recent_de_ratio < 1.5:  # 较高但仍合理的债务 - Higher but still reasonable debt
            score += 1
            details.append(f"Moderate debt level: D/E ratio of {recent_de_ratio:.2f}")
        else:
            details.append(f"High debt level: D/E ratio of {recent_de_ratio:.2f}")
    else:
        details.append("Missing debt or equity data")
    
    # 3. 现金管理效率 - 芒格重视适当的现金水平
    # Cash management efficiency - Munger values appropriate cash levels
    cash_values = [item.cash_and_equivalents for item in financial_line_items
                  if hasattr(item, 'cash_and_equivalents') and item.cash_and_equivalents is not None]
    revenue_values = [item.revenue for item in financial_line_items
                     if hasattr(item, 'revenue') and item.revenue is not None]
    
    if cash_values and revenue_values and len(cash_values) > 0 and len(revenue_values) > 0:
        # 计算现金收入比（芒格认为大多数企业适宜的比例为10-20%）
        # Calculate cash to revenue ratio (Munger likes 10-20% for most businesses)
        cash_to_revenue = cash_values[0] / revenue_values[0] if revenue_values[0] > 0 else 0
        
        if 0.1 <= cash_to_revenue <= 0.25:
            # 黄金地带 - 不太多，不太少 - Goldilocks zone - not too much, not too little
            score += 2
            details.append(f"Prudent cash management: Cash/Revenue ratio of {cash_to_revenue:.2f}")
        elif 0.05 <= cash_to_revenue < 0.1 or 0.25 < cash_to_revenue <= 0.4:
            # 合理但不理想 - Reasonable but not ideal
            score += 1
            details.append(f"Acceptable cash position: Cash/Revenue ratio of {cash_to_revenue:.2f}")
        elif cash_to_revenue > 0.4:
            # 现金过多 - 可能资本配置效率低下 - Too much cash - potentially inefficient capital allocation
            details.append(f"Excess cash reserves: Cash/Revenue ratio of {cash_to_revenue:.2f}")
        else:
            # 现金太少 - 可能有风险 - Too little cash - potentially risky
            details.append(f"Low cash reserves: Cash/Revenue ratio of {cash_to_revenue:.2f}")
    else:
        details.append("Insufficient cash or revenue data")
    
    # 4. 内部人员活动 - 芒格重视利益一致性 - Insider activity - Munger values skin in the game
    if insider_trades and len(insider_trades) > 0:
        # 统计买入vs卖出 - Count buys vs. sells
        buys = sum(1 for trade in insider_trades if hasattr(trade, 'transaction_type') and 
                   trade.transaction_type and trade.transaction_type.lower() in ['buy', 'purchase'])
        sells = sum(1 for trade in insider_trades if hasattr(trade, 'transaction_type') and 
                    trade.transaction_type and trade.transaction_type.lower() in ['sell', 'sale'])
        
        # 计算买入比例 - Calculate the buy ratio
        total_trades = buys + sells
        if total_trades > 0:
            buy_ratio = buys / total_trades
            if buy_ratio > 0.7:  # 强烈的内部人员买入 - Strong insider buying
                score += 2
                details.append(f"Strong insider buying: {buys}/{total_trades} transactions are purchases")
            elif buy_ratio > 0.4:  # 平衡的内部人员活动 - Balanced insider activity
                score += 1
                details.append(f"Balanced insider trading: {buys}/{total_trades} transactions are purchases")
            elif buy_ratio < 0.1 and sells > 5:  # 大量卖出 - Heavy selling
                score -= 1  # 过度卖出的惩罚 - Penalty for excessive selling
                details.append(f"Concerning insider selling: {sells}/{total_trades} transactions are sales")
            else:
                details.append(f"Mixed insider activity: {buys}/{total_trades} transactions are purchases")
        else:
            details.append("No recorded insider transactions")
    else:
        details.append("No insider trading data available")
    
    # 5. 股数一致性 - 芒格偏好稳定/减少的股数
    # Consistency in share count - Munger prefers stable/decreasing shares
    share_counts = [item.outstanding_shares for item in financial_line_items
                   if hasattr(item, 'outstanding_shares') and item.outstanding_shares is not None]
    
    if share_counts and len(share_counts) >= 3:
        if share_counts[0] < share_counts[-1] * 0.95:  # 股数减少5%以上 - 5%+ reduction in shares
            score += 2
            details.append("Shareholder-friendly: Reducing share count over time")
        elif share_counts[0] < share_counts[-1] * 1.05:  # 稳定的股数 - Stable share count
            score += 1
            details.append("Stable share count: Limited dilution")
        elif share_counts[0] > share_counts[-1] * 1.2:  # 稀释超过20% - >20% dilution
            score -= 1  # 过度稀释的惩罚 - Penalty for excessive dilution
            details.append("Concerning dilution: Share count increased significantly")
        else:
            details.append("Moderate share count increase over time")
    else:
        details.append("Insufficient share count data")
    
    # 将评分标准化到0-10范围 - Scale score to 0-10 range
    # 最大可能原始分数为12 (3+3+2+2+2) - Maximum possible raw score would be 12 (3+3+2+2+2)
    final_score = max(0, min(10, score * 10 / 12))
    
    return {
        "score": final_score,
        "details": "; ".join(details)
    }


def analyze_predictability(financial_line_items: list) -> dict:
    """
    Assess the predictability of the business - Munger strongly prefers businesses
    whose future operations and cashflows are relatively easy to predict.
    """
    score = 0
    details = []
    
    if not financial_line_items or len(financial_line_items) < 5:
        return {
            "score": 0,
            "details": "Insufficient data to analyze business predictability (need 5+ years)"
        }
    
    # 1. Revenue stability and growth
    revenues = [item.revenue for item in financial_line_items 
               if hasattr(item, 'revenue') and item.revenue is not None]
    
    if revenues and len(revenues) >= 5:
        # Calculate year-over-year growth rates
        growth_rates = [(revenues[i] / revenues[i+1] - 1) for i in range(len(revenues)-1)]
        
        avg_growth = sum(growth_rates) / len(growth_rates)
        growth_volatility = sum(abs(r - avg_growth) for r in growth_rates) / len(growth_rates)
        
        if avg_growth > 0.05 and growth_volatility < 0.1:
            # Steady, consistent growth (Munger loves this)
            score += 3
            details.append(f"Highly predictable revenue: {avg_growth:.1%} avg growth with low volatility")
        elif avg_growth > 0 and growth_volatility < 0.2:
            # Positive but somewhat volatile growth
            score += 2
            details.append(f"Moderately predictable revenue: {avg_growth:.1%} avg growth with some volatility")
        elif avg_growth > 0:
            # Growing but unpredictable
            score += 1
            details.append(f"Growing but less predictable revenue: {avg_growth:.1%} avg growth with high volatility")
        else:
            details.append(f"Declining or highly unpredictable revenue: {avg_growth:.1%} avg growth")
    else:
        details.append("Insufficient revenue history for predictability analysis")
    
    # 2. Operating income stability
    op_income = [item.operating_income for item in financial_line_items 
                if hasattr(item, 'operating_income') and item.operating_income is not None]
    
    if op_income and len(op_income) >= 5:
        # Count positive operating income periods
        positive_periods = sum(1 for income in op_income if income > 0)
        
        if positive_periods == len(op_income):
            # Consistently profitable operations
            score += 3
            details.append("Highly predictable operations: Operating income positive in all periods")
        elif positive_periods >= len(op_income) * 0.8:
            # Mostly profitable operations
            score += 2
            details.append(f"Predictable operations: Operating income positive in {positive_periods}/{len(op_income)} periods")
        elif positive_periods >= len(op_income) * 0.6:
            # Somewhat profitable operations
            score += 1
            details.append(f"Somewhat predictable operations: Operating income positive in {positive_periods}/{len(op_income)} periods")
        else:
            details.append(f"Unpredictable operations: Operating income positive in only {positive_periods}/{len(op_income)} periods")
    else:
        details.append("Insufficient operating income history")
    
    # 3. Margin consistency - Munger values stable margins
    op_margins = [item.operating_margin for item in financial_line_items 
                 if hasattr(item, 'operating_margin') and item.operating_margin is not None]
    
    if op_margins and len(op_margins) >= 5:
        # Calculate margin volatility
        avg_margin = sum(op_margins) / len(op_margins)
        margin_volatility = sum(abs(m - avg_margin) for m in op_margins) / len(op_margins)
        
        if margin_volatility < 0.03:  # Very stable margins
            score += 2
            details.append(f"Highly predictable margins: {avg_margin:.1%} avg with minimal volatility")
        elif margin_volatility < 0.07:  # Moderately stable margins
            score += 1
            details.append(f"Moderately predictable margins: {avg_margin:.1%} avg with some volatility")
        else:
            details.append(f"Unpredictable margins: {avg_margin:.1%} avg with high volatility ({margin_volatility:.1%})")
    else:
        details.append("Insufficient margin history")
    
    # 4. Cash generation reliability
    fcf_values = [item.free_cash_flow for item in financial_line_items 
                 if hasattr(item, 'free_cash_flow') and item.free_cash_flow is not None]
    
    if fcf_values and len(fcf_values) >= 5:
        # Count positive FCF periods
        positive_fcf_periods = sum(1 for fcf in fcf_values if fcf > 0)
        
        if positive_fcf_periods == len(fcf_values):
            # Consistently positive FCF
            score += 2
            details.append("Highly predictable cash generation: Positive FCF in all periods")
        elif positive_fcf_periods >= len(fcf_values) * 0.8:
            # Mostly positive FCF
            score += 1
            details.append(f"Predictable cash generation: Positive FCF in {positive_fcf_periods}/{len(fcf_values)} periods")
        else:
            details.append(f"Unpredictable cash generation: Positive FCF in only {positive_fcf_periods}/{len(fcf_values)} periods")
    else:
        details.append("Insufficient free cash flow history")
    
    # Scale score to 0-10 range
    # Maximum possible raw score would be 10 (3+3+2+2)
    final_score = min(10, score * 10 / 10)
    
    return {
        "score": final_score,
        "details": "; ".join(details)
    }


def calculate_munger_valuation(financial_line_items: list, market_cap: float) -> dict:
    """
    Calculate intrinsic value using Munger's approach:
    - Focus on owner earnings (approximated by FCF)
    - Simple multiple on normalized earnings
    - Prefer paying a fair price for a wonderful business
    """
    score = 0
    details = []
    
    if not financial_line_items or market_cap is None:
        return {
            "score": 0,
            "details": "Insufficient data to perform valuation"
        }
    
    # Get FCF values (Munger's preferred "owner earnings" metric)
    fcf_values = [item.free_cash_flow for item in financial_line_items 
                 if hasattr(item, 'free_cash_flow') and item.free_cash_flow is not None]
    
    if not fcf_values or len(fcf_values) < 3:
        return {
            "score": 0,
            "details": "Insufficient free cash flow data for valuation"
        }
    
    # 1. Normalize earnings by taking average of last 3-5 years
    # (Munger prefers to normalize earnings to avoid over/under-valuation based on cyclical factors)
    normalized_fcf = sum(fcf_values[:min(5, len(fcf_values))]) / min(5, len(fcf_values))
    
    if normalized_fcf <= 0:
        return {
            "score": 0,
            "details": f"Negative or zero normalized FCF ({normalized_fcf}), cannot value",
            "intrinsic_value": None
        }
    
    # 2. Calculate FCF yield (inverse of P/FCF multiple)
    fcf_yield = normalized_fcf / market_cap
    
    # 3. Apply Munger's FCF multiple based on business quality
    # Munger would pay higher multiples for wonderful businesses
    # Let's use a sliding scale where higher FCF yields are more attractive
    if fcf_yield > 0.08:  # >8% FCF yield (P/FCF < 12.5x)
        score += 4
        details.append(f"Excellent value: {fcf_yield:.1%} FCF yield")
    elif fcf_yield > 0.05:  # >5% FCF yield (P/FCF < 20x)
        score += 3
        details.append(f"Good value: {fcf_yield:.1%} FCF yield")
    elif fcf_yield > 0.03:  # >3% FCF yield (P/FCF < 33x)
        score += 1
        details.append(f"Fair value: {fcf_yield:.1%} FCF yield")
    else:
        details.append(f"Expensive: Only {fcf_yield:.1%} FCF yield")
    
    # 4. Calculate simple intrinsic value range
    # Munger tends to use straightforward valuations, avoiding complex DCF models
    conservative_value = normalized_fcf * 10  # 10x FCF = 10% yield
    reasonable_value = normalized_fcf * 15    # 15x FCF ≈ 6.7% yield
    optimistic_value = normalized_fcf * 20    # 20x FCF = 5% yield
    
    # 5. Calculate margins of safety
    current_to_reasonable = (reasonable_value - market_cap) / market_cap
    
    if current_to_reasonable > 0.3:  # >30% upside
        score += 3
        details.append(f"Large margin of safety: {current_to_reasonable:.1%} upside to reasonable value")
    elif current_to_reasonable > 0.1:  # >10% upside
        score += 2
        details.append(f"Moderate margin of safety: {current_to_reasonable:.1%} upside to reasonable value")
    elif current_to_reasonable > -0.1:  # Within 10% of reasonable value
        score += 1
        details.append(f"Fair price: Within 10% of reasonable value ({current_to_reasonable:.1%})")
    else:
        details.append(f"Expensive: {-current_to_reasonable:.1%} premium to reasonable value")
    
    # 6. Check earnings trajectory for additional context
    # Munger likes growing owner earnings
    if len(fcf_values) >= 3:
        recent_avg = sum(fcf_values[:3]) / 3
        older_avg = sum(fcf_values[-3:]) / 3 if len(fcf_values) >= 6 else fcf_values[-1]
        
        if recent_avg > older_avg * 1.2:  # >20% growth in FCF
            score += 3
            details.append("Growing FCF trend adds to intrinsic value")
        elif recent_avg > older_avg:
            score += 2
            details.append("Stable to growing FCF supports valuation")
        else:
            details.append("Declining FCF trend is concerning")
    
    # Scale score to 0-10 range
    # Maximum possible raw score would be 10 (4+3+3)
    final_score = min(10, score * 10 / 10) 
    
    return {
        "score": final_score,
        "details": "; ".join(details),
        "intrinsic_value_range": {
            "conservative": conservative_value,
            "reasonable": reasonable_value,
            "optimistic": optimistic_value
        },
        "fcf_yield": fcf_yield,
        "normalized_fcf": normalized_fcf
    }


def analyze_news_sentiment(news_items: list) -> str:
    """
    Simple qualitative analysis of recent news.
    Munger pays attention to significant news but doesn't overreact to short-term stories.
    """
    if not news_items or len(news_items) == 0:
        return "No news data available"
    
    # Just return a simple count for now - in a real implementation, this would use NLP
    return f"Qualitative review of {len(news_items)} recent news items would be needed"


# 移除了 model_name 和 model_provider 参数，因为模型固定为 GPT-4o
# Removed model_name and model_provider parameters as the model is fixed to GPT-4o
def generate_munger_output(
    ticker: str,
    analysis_data: dict[str, any],
    # model_name: str, # 已移除 (Removed)
    # model_provider: str, # 已移除 (Removed)
) -> CharlieMungerSignal:
    """
    Generates investment decisions in the style of Charlie Munger.
    """
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是查理·芒格的人工智能代理，运用他的原则进行投资决策：

            1. 关注业务的质量和可预测性。
            2. 运用多种学科的思维模型来分析投资。
            3. 寻找强大且持久的竞争优势（护城河）。
            4. 强调长远的思考和耐心。
            5. 重视管理层的诚信和能力。
            6. 优先考虑投资回报率高的企业。
            7. 为优秀的企业支付合理的价格。
            8. 切勿出价过高，始终要求安全边际。
            9. 避免复杂业务和你不了解的业务。
            10. “逆向思维，永远逆向思维”——专注于避免愚蠢，而不是追求卓越。

            规则：
            - 赞扬运营和现金流可预测、稳定的企业。
            - 重视高投资回报率和定价能力的企业。
            - 青睐经济状况易于理解的简单企业。
            - 欣赏那些积极参与并注重股东利益的资本配置的管理层。
            - 关注长期经济效益而非短期指标。
            - 对动态快速变化或股权稀释过度的企业保持警惕。
            - 避免过度杠杆或金融工程。
            - 提供理性的、基于数据的建议（看涨、看跌或中性）。"""
        ),
        (
            "human",
            """根据以下分析，创建芒格式的投资信号。

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

    def create_default_charlie_munger_signal():
        return CharlieMungerSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="Error in analysis, defaulting to neutral"
        )

    # 调用 call_llm 时不再传递 model_name 和 model_provider
    # model_name and model_provider are no longer passed when calling call_llm
    return call_llm(
        prompt=prompt, 
        # model_name=model_name, # 已移除 (Removed)
        # model_provider=model_provider, # 已移除 (Removed)
        pydantic_model=CharlieMungerSignal, 
        agent_name="charlie_munger_agent", 
        default_factory=create_default_charlie_munger_signal,
    )