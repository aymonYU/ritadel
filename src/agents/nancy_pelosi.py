from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
import json
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm

from tools.api import get_financial_metrics, get_market_cap, search_line_items, get_company_news, get_insider_trades

"""
Nancy Pelosi政策信息优势分析师代理 - 基于政策内部信息和国会交易模式
Nancy Pelosi policy information advantage analyst agent - Based on policy insider information and congressional trading patterns
"""

class NancyPelosiSignal(BaseModel):
    """
    Nancy Pelosi分析信号模型 - 包含投资信号、置信度和推理
    Nancy Pelosi analysis signal model - Contains investment signal, confidence and reasoning
    """
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def nancy_pelosi_agent(state: AgentState):
    """
    使用政策信息优势和国会交易模式分析股票：
    1. 利用政策内部知识识别监管套利机会
    2. 识别在立法或拨款中获得优待的行业
    3. 分析与政府关系密切且有重大合同的公司
    4. 在公开披露前识别信息不对称机会
    5. 跟踪实际国会交易模式以确认投资信号
    
    Analyzes stocks using policy information advantage and congressional trading patterns:
    1. Regulatory arbitrage opportunities from insider policy knowledge
    2. Sectors receiving preferential treatment in legislation or appropriations
    3. Companies with significant government relationships and contracts
    4. Identifies asymmetric information opportunities before public disclosure
    5. Tracks actual congressional trading patterns for signal confirmation
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    
    # 收集分析数据 - Collect analysis data
    analysis_data = {}
    pelosi_analysis = {}
    
    for ticker in tickers:
        progress.update_status("nancy_pelosi_agent", ticker, "Fetching financial metrics")
        # 获取所需数据 - Fetch required data
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=5)
        
        progress.update_status("nancy_pelosi_agent", ticker, "Gathering financial line items")
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",  # 收入
                "net_income",  # 净收入
                "outstanding_shares",  # 流通股数
                "total_assets",  # 总资产
                "research_and_development",  # 研发费用
                "goodwill_and_intangible_assets",  # 商誉和无形资产 - 政府承包商通常较高
            ],
            end_date,
            period="annual",
            limit=5,
        )
        
        progress.update_status("nancy_pelosi_agent", ticker, "Getting market cap")
        market_cap = get_market_cap(ticker, end_date)
        
        progress.update_status("nancy_pelosi_agent", ticker, "Getting recent news")
        # 分析最近新闻中的政策/监管提及 - Analysis of recent news for policy/regulatory mentions
        company_news = get_company_news(ticker, end_date, limit=100)
        
        progress.update_status("nancy_pelosi_agent", ticker, "Fetching insider trading data")
        # 获取内部交易数据以识别模式 - Get insider trading data to identify patterns
        insider_trades = get_insider_trades(ticker, end_date, limit=100)
        
        progress.update_status("nancy_pelosi_agent", ticker, "Analyzing legislation impact")
        # 分析立法影响 - Analyze legislation impact
        legislation_analysis = analyze_legislation_impact(company_news, ticker)
        
        progress.update_status("nancy_pelosi_agent", ticker, "Analyzing government contract potential")
        # 分析政府合同潜力 - Analyze government contract potential
        gov_contract_analysis = analyze_government_contracts(financial_line_items, company_news)
        
        progress.update_status("nancy_pelosi_agent", ticker, "Analyzing policy trends")
        # 分析政策趋势 - Analyze policy trends
        policy_analysis = analyze_policy_trends(company_news, ticker)

        progress.update_status("nancy_pelosi_agent", ticker, "Analyzing information asymmetry")
        # 分析信息不对称 - Analyze information asymmetry
        asymmetry_analysis = analyze_information_asymmetry(company_news, insider_trades, ticker)
        
        progress.update_status("nancy_pelosi_agent", ticker, "Analyzing congressional trading patterns")
        # 分析国会交易模式 - Analyze congressional trading patterns
        congressional_trading = analyze_congressional_trading(ticker, insider_trades, company_news)
        
        # 计算总分，信息不对称和国会交易权重更高 - Calculate total score with higher weight on information asymmetry and congressional trading
        total_score = (
            legislation_analysis["score"] * 0.2 +  # 立法分析权重20% - Legislation analysis weight 20%
            gov_contract_analysis["score"] * 0.2 +  # 政府合同分析权重20% - Government contract analysis weight 20%
            policy_analysis["score"] * 0.2 +  # 政策分析权重20% - Policy analysis weight 20%
            asymmetry_analysis["score"] * 0.2 +  # 信息不对称分析权重20% - Information asymmetry analysis weight 20%
            congressional_trading["score"] * 0.2  # 国会交易分析权重20% - Congressional trading analysis weight 20%
        )
        max_possible_score = 10
        
        # 生成交易信号 - Generate trading signal
        if total_score >= 0.65 * max_possible_score:  # 较低阈值 - 偏向于行动 - Lower threshold - biased toward action
            signal = "bullish"
        elif total_score <= 0.35 * max_possible_score:
            signal = "bearish"
        else:
            signal = "neutral"
        
        # 整合所有分析结果 - Combine all analysis results
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "legislation_analysis": legislation_analysis,
            "gov_contract_analysis": gov_contract_analysis,
            "policy_analysis": policy_analysis,
            "asymmetry_analysis": asymmetry_analysis,
            "congressional_trading": congressional_trading,
            "market_cap": market_cap,
        }
        
        progress.update_status("nancy_pelosi_agent", ticker, "Generating congressional trading analysis")
        pelosi_output = generate_pelosi_output(
            ticker=ticker,
            analysis_data=analysis_data,
        )
        
        # 以与其他代理一致的格式存储分析 - Store analysis in consistent format with other agents
        pelosi_analysis[ticker] = {
            "signal": pelosi_output.signal,
            "confidence": pelosi_output.confidence,
            "reasoning": pelosi_output.reasoning,
        }
        
        progress.update_status("nancy_pelosi_agent", ticker, "Done")
    
    # 创建消息 - Create the message
    message = HumanMessage(
        content=json.dumps(pelosi_analysis),
        name="nancy_pelosi_agent"
    )
    
    # 如果请求，显示推理过程 - Show reasoning if requested
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(pelosi_analysis, "Nancy Pelosi Agent")
    
    # 将信号添加到analyst_signals列表 - Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["nancy_pelosi_agent"] = pelosi_analysis
    
    return {
        "messages": [message],
        "data": state["data"]
    }


def analyze_legislation_impact(company_news: list, ticker: str) -> dict:
    """
    分析最近新闻中影响公司的政策或监管变化的提及。
    专注于识别可能创造盈利机会的政策变化的预公开信息。
    
    Analyze recent news for mentions of policy or regulatory changes affecting the company.
    Focus on identifying pre-public information about policy changes that could create profit opportunities.
    """
    if not company_news:
        return {
            "score": 0,
            "details": "No news data available for legislation analysis"
        }
    
    # 与政策和立法相关的关键词 - Keywords related to policy and legislation
    legislation_keywords = [
        "bill", "act", "legislation", "congress", "senate", "house", "regulation", 
        "regulatory", "policy", "subsidies", "tax credit", "incentive", "stimulus",
        "appropriation", "federal funding", "government program", "committee hearing",
        "draft legislation", "upcoming vote", "markup session", "lobbying",
        "earmark", "omnibus", "reconciliation"
    ]
    
    # 评分参数 - Score parameters
    score = 0
    relevant_news_count = 0
    positive_legislation_count = 0
    negative_legislation_count = 0
    details = []
    
    # 立法分析 - Legislation analysis
    for news in company_news:
        title_lower = news.title.lower()
        
        # 检查立法相关新闻 - Check for legislation-related news
        if any(keyword in title_lower for keyword in legislation_keywords):
            relevant_news_count += 1
            
            # 对立法影响的情感进行评分 - Score the sentiment for legislation impact
            sentiment = news.sentiment if hasattr(news, 'sentiment') and news.sentiment else "neutral"
            
            if sentiment == "positive":
                positive_legislation_count += 1
                score += 1
                details.append(f"Positive legislation impact: {news.title}")
            elif sentiment == "negative":
                negative_legislation_count += 1
                score -= 1
                details.append(f"Negative legislation impact: {news.title}")
    
    # 重大立法活动的额外加分 - Additional score boost for significant legislative activity
    if relevant_news_count > 5:
        score += 1
        details.append(f"High legislative activity: {relevant_news_count} relevant news items")
    
    # Calculate net sentiment
    net_sentiment = positive_legislation_count - negative_legislation_count
    
    # Interpret the results in more direct terms
    if net_sentiment > 3:
        score += 3
        details.append(f"Highly favorable legislative outlook: +{net_sentiment} - positions before public awareness advisable")
    elif net_sentiment > 0:
        score += 2
        details.append(f"Positive legislative outlook: +{net_sentiment} - early strategic positioning recommended")
    elif net_sentiment < -3:
        score -= 2
        details.append(f"Highly unfavorable legislative outlook: {net_sentiment} - consider defensive positioning")
    elif net_sentiment < 0:
        score -= 1
        details.append(f"Negative legislative outlook: {net_sentiment} - portfolio adjustments may be prudent")
    
    return {
        "score": max(0, score),  # Ensure score is not negative
        "details": "; ".join(details) if details else "No significant legislative impacts detected",
        "relevant_news_count": relevant_news_count,
        "positive_legislation_count": positive_legislation_count,
        "negative_legislation_count": negative_legislation_count
    }


def analyze_government_contracts(financial_line_items: list, company_news: list) -> dict:
    """
    分析公司获得政府合同的潜力。
    
    寻找：
    1. 政府承包历史
    2. 新闻中潜在合同的提及
    3. 政府业务依赖的财务指标
    4. 与关键政府采购官员的关系
    
    Analyze company's potential for securing government contracts.
    
    Looks for:
    1. History of government contracting
    2. Mentions of potential contracts in news
    3. Financial indicators of government business dependence
    4. Relationships with key government procurement officials
    """
    score = 0
    details = []
    
    # 合同相关新闻关键词 - Contract-related news keywords
    contract_keywords = [
        "contract", "procurement", "award", "bid", "tender", "government deal", 
        "federal contract", "defense contract", "agency award", "government client",
        "government purchase", "government supplier", "vendor", "appropriation",
        "request for proposal", "RFP", "no-bid contract", "sole source"
    ]
    
    # 检查合同相关新闻 - Check for contract-related news
    contract_news_count = 0
    if company_news:
        for news in company_news:
            title_lower = news.title.lower()
            if any(keyword in title_lower for keyword in contract_keywords):
                contract_news_count += 1
                details.append(f"Contract potential indicated in news: {news.title}")
    
    if contract_news_count > 3:
        score += 3
        details.append(f"Significant contract news: {contract_news_count} related items")
    elif contract_news_count > 0:
        score += 1
        details.append(f"Some contract news: {contract_news_count} related items")
    
    # 分析财务数据以寻找政府合同指标 - Analyze financial data for government contract indicators
    if financial_line_items and len(financial_line_items) > 0:
        # 高商誉通常表明收购了政府承包商 - High goodwill often indicates acquisitions of government contractors
        if hasattr(financial_line_items[0], 'goodwill_and_intangible_assets') and financial_line_items[0].goodwill_and_intangible_assets:
            goodwill_to_assets_ratio = financial_line_items[0].goodwill_and_intangible_assets / financial_line_items[0].total_assets if financial_line_items[0].total_assets else 0
            
            if goodwill_to_assets_ratio > 0.3:
                score += 1
                details.append(f"High goodwill ratio ({goodwill_to_assets_ratio:.2f}) suggests acquisitions of contracted businesses")
        
        # 稳定的收入模式通常表明长期政府合同 - Stable revenue patterns often indicate long-term government contracts
        revenues = [item.revenue for item in financial_line_items if hasattr(item, 'revenue') and item.revenue is not None]
        if len(revenues) >= 3:
            revenue_volatility = sum(abs((revenues[i] / revenues[i+1]) - 1) for i in range(len(revenues)-1)) / (len(revenues)-1) if all(r > 0 for r in revenues) else 1
            
            if revenue_volatility < 0.1:
                score += 2
                details.append(f"Highly stable revenue pattern (volatility: {revenue_volatility:.2f}) suggests long-term contracts")
            elif revenue_volatility < 0.2:
                score += 1
                details.append(f"Relatively stable revenue (volatility: {revenue_volatility:.2f}) suggests possible contract base")
    
    # 将合同潜力与投资建议联系起来 - Connect contract potential to investment recommendation
    if score >= 4:
        details.append("Strong government contracting position represents significant profit opportunity")
    elif score >= 2:
        details.append("Moderate government contracting potential indicates possible profit opportunity")
    
    return {
        "score": score,
        "details": "; ".join(details) if details else "No significant government contract potential detected"
    }


def analyze_policy_trends(company_news: list, ticker: str) -> dict:
    """
    分析可能影响公司前景的更广泛政策趋势
    
    检查行业范围内的政策变化、监管环境，
    以及可能影响未来表现的政府优先事项。
    
    Analyze broader policy trends that might affect the company's prospects
    
    Examines sector-wide policy changes, regulatory environments,
    and government priorities that could impact future performance.
    """
    score = 0
    details = []
    
    # 经常受到政府行动影响的政策领域关键词 - Keywords for policy areas often subject to government action
    policy_areas = {
        'technology': ['tech', 'technology', 'software', 'data', 'privacy', 'cybersecurity', 'ai', 'artificial intelligence'],
        'healthcare': ['health', 'medical', 'medicare', 'medicaid', 'affordable care', 'pharma', 'drug', 'vaccine'],
        'finance': ['bank', 'financial', 'credit', 'loan', 'interest rate', 'federal reserve', 'treasury'],
        'energy': ['energy', 'oil', 'gas', 'renewable', 'solar', 'wind', 'climate', 'carbon', 'emissions'],
        'infrastructure': ['infrastructure', 'construction', 'transportation', 'highway', 'bridge', 'road', 'rail'],
        'defense': ['defense', 'military', 'security', 'weapons', 'contractor', 'army', 'navy', 'air force']
    }
    
    # 按政策领域统计新闻 - Count news by policy area
    policy_area_counts = {area: 0 for area in policy_areas}
    trending_policy_areas = []
    
    for news in company_news:
        title_lower = news.title.lower()
        
        for area, keywords in policy_areas.items():
            if any(keyword in title_lower for keyword in keywords):
                policy_area_counts[area] += 1
    
    # 识别趋势政策领域（新闻覆盖率显著的领域）- Identify trending policy areas (areas with significant news coverage)
    for area, count in policy_area_counts.items():
        if count > 5:
            trending_policy_areas.append(area)
            score += 1
            details.append(f"Significant {area} policy activity: {count} news items - potential strategic advantage")
        elif count > 2:
            trending_policy_areas.append(area)
            score += 0.5
            details.append(f"Some {area} policy activity: {count} news items - worth monitoring closely")
    
    # 当前具有立法动力的行业的额外评分 - Additional score for sectors with current legislative momentum
    priority_sectors = ['infrastructure', 'technology', 'healthcare', 'energy']
    if any(area in priority_sectors for area in trending_policy_areas):
        score += 2
        details.append(f"Company in high-priority policy sectors: {[area for area in trending_policy_areas if area in priority_sectors]} - favorable positioning")
    
    # 政策影响分析 - Analysis of policy implications
    if len(trending_policy_areas) > 1:
        score += 1
        details.append(f"Multiple policy areas ({', '.join(trending_policy_areas)}) create cross-sector opportunities")
    
    if not company_news:
        return {
            "score": 0,
            "details": "No news data available for policy trend analysis"
        }
    
    return {
        "score": score,
        "details": "; ".join(details) if details else "No significant policy trends detected"
    }


def analyze_information_asymmetry(company_news: list, insider_trades: list, ticker: str) -> dict:
    """
    基于政策知识分析信息不对称机会。
    寻找表明潜在政策驱动信息优势的模式。
    
    这识别了政策知识在公开市场意识之前创造交易优势的机会。
    
    Analyze information asymmetry opportunities based on policy knowledge.
    Looks for patterns indicating potential policy-driven information advantage.
    
    This identifies opportunities where policy knowledge creates trading advantage 
    before public market awareness.
    """
    score = 0
    details = []
    
    # 表明潜在信息不对称的关键术语 - Key terms indicating potential information asymmetry
    asymmetry_keywords = [
        "upcoming announcement", "pending approval", "not yet public", "confidential", 
        "internal documents", "sources familiar", "expected to announce", "advance notice",
        "exclusive", "unreleased", "leaked", "to be determined", "advance knowledge",
        "preliminary results", "draft report", "early findings", "before official release",
        "closed-door meeting", "private briefing", "insider", "tip", "rumor", "not widely known"
    ]
    
    # Check for news indicating non-public information
    asymmetry_news_count = 0
    high_value_asymmetry = 0
    
    if company_news:
        for news in company_news:
            title_lower = news.title.lower()
            
            if any(keyword in title_lower for keyword in asymmetry_keywords):
                asymmetry_news_count += 1
                
                # Identify particularly valuable asymmetric information
                if any(term in title_lower for term in ["approval", "contract award", "investigation", "regulatory action"]):
                    high_value_asymmetry += 1
                    details.append(f"High-value information asymmetry: {news.title}")
    
    # Score based on potential information advantage
    if high_value_asymmetry > 0:
        score += 3
        details.append(f"Significant information advantage opportunities: {high_value_asymmetry} high-value items")
    elif asymmetry_news_count > 2:
        score += 2
        details.append(f"Multiple information advantage opportunities: {asymmetry_news_count} items")
    elif asymmetry_news_count > 0:
        score += 1
        details.append(f"Possible information advantage: {asymmetry_news_count} items")
    
    # Analyze timing patterns between news and insider activity
    if company_news and insider_trades and len(insider_trades) > 0:
        # Look for insider trading before significant news
        news_dates = [news.date for news in company_news]
        trade_dates = [trade.transaction_date for trade in insider_trades if trade.transaction_date]
        
        # Simple pattern detection - this could be enhanced with more sophisticated analysis
        pattern_detected = False
        for trade_date in trade_dates:
            for news_date in news_dates:
                if trade_date and news_date and trade_date < news_date:
                    days_diff = (datetime.strptime(news_date, "%Y-%m-%d") - datetime.strptime(trade_date, "%Y-%m-%d")).days
                    if 1 <= days_diff <= 30:  # Trading within 30 days before news
                        pattern_detected = True
                        details.append(f"Potential information timing pattern: trading activity {days_diff} days before news")
                        break
            if pattern_detected:
                score += 2
                break
    
    return {
        "score": score,
        "details": "; ".join(details) if details else "No significant information asymmetry detected"
    }


def analyze_congressional_trading(ticker: str, insider_trades: list, company_news: list) -> dict:
    """
    Analyze patterns of congressional trading and policy timing.
    Looks for relationships between insider activity and policy events.
    
    This identifies cases where congressional trading might signal future policy actions.
    """
    score = 0
    details = []
    
    # Congressional trading keywords in news
    congress_keywords = [
        "congress", "congressman", "congresswoman", "senator", "representative", 
        "house member", "committee chair", "subcommittee", "pelosi", "schumer", 
        "mcconnell", "committee", "caucus", "congressional trading", "disclosure",
        "financial disclosure", "stock act", "ethics filing"
    ]
    
    # Check for congressional trading related news
    congress_news_count = 0
    if company_news:
        for news in company_news:
            title_lower = news.title.lower()
            if any(keyword in title_lower for keyword in congress_keywords):
                congress_news_count += 1
                details.append(f"Congress-related trading news: {news.title}")
    
    if congress_news_count > 2:
        score += 3
        details.append(f"Significant congressional trading interest: {congress_news_count} related items")
    elif congress_news_count > 0:
        score += 1
        details.append(f"Some congressional trading interest: {congress_news_count} related items")
    
    # Analyze buy/sell patterns for potential information advantage
    if insider_trades and len(insider_trades) > 5:
        # Count buys vs sells
        buys = sum(1 for trade in insider_trades if trade.transaction_shares > 0)
        sells = sum(1 for trade in insider_trades if trade.transaction_shares < 0)
        
        # Calculate buy/sell ratio
        if buys + sells > 0:
            buy_ratio = buys / (buys + sells)
            
            if buy_ratio > 0.7:
                score += 3
                details.append(f"Strong insider buying pattern: {buy_ratio:.0%} buys - indicates positive information advantage")
            elif buy_ratio < 0.3:
                score -= 2
                details.append(f"Strong insider selling pattern: {(1-buy_ratio):.0%} sells - indicates negative information advantage")
    
    # 检查具有高国会交易活动的特定行业 - Check for specific sectors with high congressional trading activity
    congress_heavy_sectors = {
        "tech": ["AAPL", "MSFT", "GOOG", "GOOGL", "META", "AMZN", "NVDA"],
        "pharma": ["PFE", "JNJ", "MRK", "ABBV", "LLY"],
        "defense": ["LMT", "RTX", "NOC", "GD", "BA"],
        "energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
        "finance": ["JPM", "BAC", "GS", "MS", "WFC"]
    }
    
    for sector, tickers in congress_heavy_sectors.items():
        if ticker in tickers:
            score += 1
            details.append(f"Company in {sector} sector with high congressional trading activity")
            break
    
    # 最后，检查已知历史上国会交易频繁的股票 - Finally, check known historically high congressional trading stocks
    high_trading_stocks = ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "NVDA", "PFE", "JNJ"]
    if ticker in high_trading_stocks:
        score += 2
        details.append(f"{ticker} is among top stocks with historical congressional trading activity")
    
    return {
        "score": score,
        "details": "; ".join(details) if details else "No significant congressional trading patterns detected"
    }


# 移除了 model_name 和 model_provider 参数，因为模型固定为 GPT-4o
# Removed model_name and model_provider parameters as the model is fixed to GPT-4o
def generate_pelosi_output(
    ticker: str,
    analysis_data: dict[str, any],
    # model_name: str, # 已移除 (Removed)
    # model_provider: str, # 已移除 (Removed)
) -> NancyPelosiSignal:
    """
    基于国会交易风格生成投资决策
    Generate congressional trading style investment decision from LLM.
    """
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """You analyze stocks based on information advantage and policy knowledge:

            1. Identify regulatory arbitrage opportunities where policy knowledge creates profit
            2. Evaluate companies positioned to benefit from upcoming legislation
            3. Find asymmetric information opportunities before public market awareness
            4. Determine which companies have direct government revenue streams
            5. Track actual congressional trading patterns for confirming signals
            
            Key investment principles:
            - Use advanced knowledge of policy directions before market prices adjust
            - Identify legislation impacts on specific companies before wide awareness
            - Position ahead of government contract awards and appropriations
            - Monitor committee activities for sector impacts
            - Leverage information advantages legally but aggressively
            
            Your analysis is purely profit-focused, logical, and direct. You prioritize identifying information asymmetry that creates actionable trading opportunities.
            """
        ),
        (
            "human",
            """Based on the following policy-driven analysis, create an investment signal:

            Analysis Data for {ticker}:
            {analysis_data}

            Return the trading signal in the following JSON format:
            {{
              "signal": "bullish/bearish/neutral",
              "confidence": float (0-100),
              "reasoning": "string"
            }}
            """
        )
    ])

    # 生成提示 - Generate the prompt
    prompt = template.invoke({
        "analysis_data": json.dumps(analysis_data, indent=2),
        "ticker": ticker
    })

    # 为NancyPelosiSignal创建默认工厂 - Create default factory for NancyPelosiSignal
    def create_default_signal():
        return NancyPelosiSignal(signal="neutral", confidence=0.0, reasoning="Error in analysis, defaulting to neutral")

    # 调用 call_llm 时不再传递 model_name 和 model_provider
    # model_name and model_provider are no longer passed when calling call_llm
    return call_llm(
        prompt=prompt,
        # model_name=model_name, # 已移除 (Removed)
        # model_provider=model_provider, # 已移除 (Removed)
        pydantic_model=NancyPelosiSignal,
        agent_name="nancy_pelosi_agent",
        default_factory=create_default_signal,
    ) 