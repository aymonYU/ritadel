"""
Phil Fisher成长投资分析师代理 - 基于菲利普·费雪的投资原则
Phil Fisher growth investing analyst agent - Based on Philip Fisher's investment principles
"""
from graph.state import AgentState, show_agent_reasoning
from tools.api import (
    get_financial_metrics,
    get_market_cap,
    search_line_items,
    get_insider_trades,
    get_company_news,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm
import statistics


class PhilFisherSignal(BaseModel):
    """
    Phil Fisher分析信号模型 - 包含投资信号、置信度和推理
    Phil Fisher analysis signal model - Contains investment signal, confidence and reasoning
    """
    signal: Literal["买入", "卖出", "中性"]
    confidence: float
    reasoning: str


def phil_fisher_agent(state: AgentState):
    """
    使用菲利普·费雪的投资原则分析股票：
      - 寻找具有长期增长潜力的公司
      - 强调管理质量和研发投入
      - 关注利润率、增长一致性和杠杆率
      - 结合基本面分析和市场情绪数据
      - 返回买入/卖出/中性信号及理由

    Analyzes stocks using Philip Fisher's investment principles:
      - Seeks companies with long-term growth potential
      - Emphasizes management quality and R&D investment
      - Focuses on margins, growth consistency and leverage
      - Combines fundamental analysis with market sentiment data
      - Returns bullish/bearish/neutral signal with reasoning

    结果是买入/卖出/中性信号，以及置信度（0-100）和文本推理解释。
    The result is a bullish/bearish/neutral signal, along with a
    confidence (0–100) and a textual reasoning explanation.
    """
    data = state["data"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    analysis_data = {}
    fisher_analysis = {}

    for ticker in tickers:
        progress.update_status("phil_fisher_agent", ticker, "Fetching financial metrics")
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=5)

        progress.update_status("phil_fisher_agent", ticker, "Gathering financial line items")
        # 收集财务数据项：收入、净利润、每股收益、研发费用等
        # Collect financial data items: revenue, net income, EPS, R&D expenses, etc.
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",
                "net_income",
                "earnings_per_share",
                "free_cash_flow",
                "research_and_development",
                "operating_income",
                "operating_margin",
                "gross_margin",
                "total_debt",
                "shareholders_equity",
                "cash_and_equivalents",
                "ebit",
                "ebitda",
            ],
            end_date,
            period="annual",
            limit=5,
        )

        progress.update_status("phil_fisher_agent", ticker, "Getting market cap")
        market_cap = get_market_cap(ticker, end_date)

        progress.update_status("phil_fisher_agent", ticker, "Fetching insider trades")
        insider_trades = get_insider_trades(ticker, end_date, start_date=None, limit=50)

        progress.update_status("phil_fisher_agent", ticker, "Fetching company news")
        company_news = get_company_news(ticker, end_date, start_date=None, limit=50)

        progress.update_status("phil_fisher_agent", ticker, "Analyzing growth & quality")
        growth_quality = analyze_fisher_growth_quality(financial_line_items)

        progress.update_status("phil_fisher_agent", ticker, "Analyzing margins & stability")
        margins_stability = analyze_margins_stability(financial_line_items)

        progress.update_status("phil_fisher_agent", ticker, "Analyzing management efficiency & leverage")
        mgmt_efficiency = analyze_management_efficiency_leverage(financial_line_items)

        progress.update_status("phil_fisher_agent", ticker, "Analyzing valuation (Fisher style)")
        fisher_valuation = analyze_fisher_valuation(financial_line_items, market_cap)

        progress.update_status("phil_fisher_agent", ticker, "Analyzing insider activity")
        insider_activity = analyze_insider_activity(insider_trades)

        progress.update_status("phil_fisher_agent", ticker, "Analyzing sentiment")
        sentiment_analysis = analyze_sentiment(company_news)

        # 综合评分：权重分配
        # Comprehensive scoring: weight allocation
        total_score = (
            growth_quality["score"] * 0.30
            + margins_stability["score"] * 0.25
            + mgmt_efficiency["score"] * 0.20
            + fisher_valuation["score"] * 0.15
            + insider_activity["score"] * 0.05
            + sentiment_analysis["score"] * 0.05
        )

        max_possible_score = 10

        # 信号生成逻辑
        # Signal generation logic
        if total_score >= 7.5:
            signal = "买入"
        elif total_score <= 4.5:
            signal = "卖出"
        else:
            signal = "中性"

        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "growth_quality": growth_quality,
            "margins_stability": margins_stability,
            "management_efficiency": mgmt_efficiency,
            "valuation_analysis": fisher_valuation,
            "insider_activity": insider_activity,
            "sentiment_analysis": sentiment_analysis,
        }

        progress.update_status("phil_fisher_agent", ticker, "Generating Phil Fisher-style analysis")
        fisher_output = generate_fisher_output(
            ticker=ticker,
            analysis_data=analysis_data,
        )

        fisher_analysis[ticker] = {
            "signal": fisher_output.signal,
            "confidence": fisher_output.confidence,
            "reasoning": fisher_output.reasoning,
        }

        progress.update_status("phil_fisher_agent", ticker, "Done")

    # 包装结果
    # Wrap up results
    message = HumanMessage(content=json.dumps(fisher_analysis), name="phil_fisher_agent")

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(fisher_analysis, "Phil Fisher Agent")

    # Save signals to state
    state["data"]["analyst_signals"]["phil_fisher_agent"] = fisher_analysis
    return {"messages": [message], "data": state["data"]}


def analyze_fisher_growth_quality(financial_line_items: list) -> dict:
    """
    评估增长与质量：
    - 收入增长
    - 每股收益增长
    - 研发投入占比
    
    Evaluate growth and quality:
    - Revenue growth
    - EPS growth
    - R&D investment ratio
    """
    if not financial_line_items or len(financial_line_items) < 2:
        return {
            "score": 0,
            "details": "财务数据不足，无法评估增长与质量",
        }

    details = []
    raw_score = 0  # 原始分数（0-9），最终转换为0-10

    # 1. 收入增长（YoY）
    revenues = [getattr(fi, 'revenue', None) for fi in financial_line_items if hasattr(fi, 'revenue') and getattr(fi, 'revenue', None) is not None]
    if len(revenues) >= 2:
        latest_rev = revenues[0]
        oldest_rev = revenues[-1]
        if oldest_rev > 0:
            rev_growth = (latest_rev - oldest_rev) / abs(oldest_rev)
            if rev_growth > 0.80:
                raw_score += 3
                details.append(f"收入增长强劲：{rev_growth:.1%}")
            elif rev_growth > 0.40:
                raw_score += 2
                details.append(f"收入增长中等：{rev_growth:.1%}")
            elif rev_growth > 0.10:
                raw_score += 1
                details.append(f"收入增长轻微：{rev_growth:.1%}")
            else:
                details.append(f"收入增长微弱或负增长：{rev_growth:.1%}")
        else:
            details.append("初始收入为零或负值，无法计算增长")
    else:
        details.append("收入数据不足，无法计算增长")

    # 2. 每股收益增长（YoY）
    eps_values = [getattr(fi, 'earnings_per_share', None) for fi in financial_line_items if hasattr(fi, 'earnings_per_share') and getattr(fi, 'earnings_per_share', None) is not None]
    if len(eps_values) >= 2:
        latest_eps = eps_values[0]
        oldest_eps = eps_values[-1]
        if abs(oldest_eps) > 1e-9:
            eps_growth = (latest_eps - oldest_eps) / abs(oldest_eps)
            if eps_growth > 0.80:
                raw_score += 3
                details.append(f"每股收益增长强劲：{eps_growth:.1%}")
            elif eps_growth > 0.40:
                raw_score += 2
                details.append(f"每股收益增长中等：{eps_growth:.1%}")
            elif eps_growth > 0.10:
                raw_score += 1
                details.append(f"每股收益增长轻微：{eps_growth:.1%}")
            else:
                details.append(f"每股收益增长微弱或负增长：{eps_growth:.1%}")
        else:
            details.append("初始每股收益接近零，跳过计算")
    else:
        details.append("每股收益数据不足，无法计算增长")

    # 3. 研发投入占比
    rnd_values = [getattr(fi, 'research_and_development', None) for fi in financial_line_items if hasattr(fi, 'research_and_development') and getattr(fi, 'research_and_development', None) is not None]
    if rnd_values and revenues and len(rnd_values) == len(revenues):
        recent_rnd = rnd_values[0]
        recent_rev = revenues[0] if revenues[0] else 1e-9
        rnd_ratio = recent_rnd / recent_rev
        if 0.03 <= rnd_ratio <= 0.15:
            raw_score += 3
            details.append(f"研发投入占比合理：{rnd_ratio:.1%}")
        elif rnd_ratio > 0.15:
            raw_score += 2
            details.append(f"研发投入占比偏高：{rnd_ratio:.1%}")
        elif rnd_ratio > 0.0:
            raw_score += 1
            details.append(f"研发投入占比偏低：{rnd_ratio:.1%}")
        else:
            details.append("无显著研发投入")
    else:
        details.append("研发数据不足，无法评估")

    # 转换为0-10分
    final_score = min(10, (raw_score / 9) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_margins_stability(financial_line_items: list) -> dict:
    """
    评估利润率稳定性：
    - 营业利润率
    - 毛利率
    - 多年度稳定性
    
    Evaluate margin stability:
    - Operating margin
    - Gross margin
    - Multi-year stability
    """
    if not financial_line_items or len(financial_line_items) < 2:
        return {
            "score": 0,
            "details": "数据不足，无法评估利润率稳定性",
        }

    details = []
    raw_score = 0  # 原始分数（0-6），最终转换为0-10

    # 1. 营业利润率一致性
    op_margins = [getattr(fi, 'operating_margin', None) for fi in financial_line_items if hasattr(fi, 'operating_margin') and getattr(fi, 'operating_margin', None) is not None]
    if len(op_margins) >= 2:
        oldest_op_margin = op_margins[-1]
        newest_op_margin = op_margins[0]
        if newest_op_margin >= oldest_op_margin > 0:
            raw_score += 2
            details.append(f"营业利润率稳定或提升：{oldest_op_margin:.1%} -> {newest_op_margin:.1%}")
        elif newest_op_margin > 0:
            raw_score += 1
            details.append(f"营业利润率为正但略有下降")
        else:
            details.append(f"营业利润率可能为负或不确定")
    else:
        details.append("营业利润率数据不足")

    # 2. 毛利率水平
    gm_values = [getattr(fi, 'gross_margin', None) for fi in financial_line_items if hasattr(fi, 'gross_margin') and getattr(fi, 'gross_margin', None) is not None]
    if gm_values:
        recent_gm = gm_values[0]
        if recent_gm > 0.5:
            raw_score += 2
            details.append(f"毛利率较高：{recent_gm:.1%}")
        elif recent_gm > 0.3:
            raw_score += 1
            details.append(f"毛利率中等：{recent_gm:.1%}")
        else:
            details.append(f"毛利率较低：{recent_gm:.1%}")
    else:
        details.append("无毛利率数据")

    # 3. 多年度利润率稳定性
    if len(op_margins) >= 3:
        stdev = statistics.pstdev(op_margins)
        if stdev < 0.02:
            raw_score += 2
            details.append("营业利润率多年稳定")
        elif stdev < 0.05:
            raw_score += 1
            details.append("营业利润率较为稳定")
        else:
            details.append("营业利润率波动较大")
    else:
        details.append("数据不足，无法评估多年稳定性")

    # 转换为0-10分
    final_score = min(10, (raw_score / 6) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_management_efficiency_leverage(financial_line_items: list) -> dict:
    """
    评估管理效率与杠杆：
    - 净资产收益率（ROE）
    - 负债权益比
    - 自由现金流一致性
    
    Evaluate management efficiency and leverage:
    - Return on Equity (ROE)
    - Debt-to-equity ratio
    - Free cash flow consistency
    """
    if not financial_line_items:
        return {
            "score": 0,
            "details": "数据不足，无法评估管理效率",
        }

    details = []
    raw_score = 0  # 原始分数（0-6），最终转换为0-10

    # 1. 净资产收益率（ROE）
    ni_values = [getattr(fi, 'net_income', None) for fi in financial_line_items if hasattr(fi, 'net_income') and getattr(fi, 'net_income', None) is not None]
    eq_values = [getattr(fi, 'shareholders_equity', None) for fi in financial_line_items if hasattr(fi, 'shareholders_equity') and getattr(fi, 'shareholders_equity', None) is not None]
    if ni_values and eq_values and len(ni_values) == len(eq_values):
        recent_ni = ni_values[0]
        recent_eq = eq_values[0] if eq_values[0] else 1e-9
        if recent_ni > 0:
            roe = recent_ni / recent_eq
            if roe > 0.2:
                raw_score += 3
                details.append(f"ROE较高：{roe:.1%}")
            elif roe > 0.1:
                raw_score += 2
                details.append(f"ROE中等：{roe:.1%}")
            elif roe > 0:
                raw_score += 1
                details.append(f"ROE较低但为正：{roe:.1%}")
            else:
                details.append(f"ROE接近零或负值：{roe:.1%}")
        else:
            details.append("净利润为零或负值，影响ROE")
    else:
        details.append("数据不足，无法计算ROE")

    # 2. 负债权益比
    debt_values = [getattr(fi, 'total_debt', None) for fi in financial_line_items if hasattr(fi, 'total_debt') and getattr(fi, 'total_debt', None) is not None]
    if debt_values and eq_values and len(debt_values) == len(eq_values):
        recent_debt = debt_values[0]
        recent_equity = eq_values[0] if eq_values[0] else 1e-9
        dte = recent_debt / recent_equity
        if dte < 0.3:
            raw_score += 2
            details.append(f"负债权益比较低：{dte:.2f}")
        elif dte < 1.0:
            raw_score += 1
            details.append(f"负债权益比适中：{dte:.2f}")
        else:
            details.append(f"负债权益比较高：{dte:.2f}")
    else:
        details.append("数据不足，无法计算负债权益比")

    # 3. 自由现金流一致性
    fcf_values = [getattr(fi, 'free_cash_flow', None) for fi in financial_line_items if hasattr(fi, 'free_cash_flow') and getattr(fi, 'free_cash_flow', None) is not None]
    if fcf_values and len(fcf_values) >= 2:
        positive_fcf_count = sum(1 for x in fcf_values if x and x > 0)
        ratio = positive_fcf_count / len(fcf_values)
        if ratio > 0.8:
            raw_score += 1
            details.append(f"多数期间自由现金流为正：{positive_fcf_count}/{len(fcf_values)}")
        else:
            details.append(f"自由现金流不稳定或经常为负")
    else:
        details.append("自由现金流数据不足")

    # 转换为0-10分
    final_score = min(10, (raw_score / 6) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_fisher_valuation(financial_line_items: list, market_cap: float | None) -> dict:
    """
    评估估值（Phil Fisher风格）：
    - 市盈率（P/E）
    - 自由现金流比率（P/FCF）
    
    Evaluate valuation (Phil Fisher style):
    - Price-to-earnings ratio (P/E)
    - Price-to-free cash flow ratio (P/FCF)
    """
    if not financial_line_items or market_cap is None:
        return {"score": 0, "details": "数据不足，无法评估估值"}

    details = []
    raw_score = 0

    # 1) 市盈率（P/E）
    net_incomes = [getattr(fi, 'net_income', None) for fi in financial_line_items if hasattr(fi, 'net_income') and getattr(fi, 'net_income', None) is not None]
    recent_net_income = net_incomes[0] if net_incomes else None
    if recent_net_income and recent_net_income > 0:
        pe = market_cap / recent_net_income
        pe_points = 0
        if pe < 20:
            pe_points = 2
            details.append(f"市盈率合理：{pe:.2f}")
        elif pe < 30:
            pe_points = 1
            details.append(f"市盈率偏高但可接受：{pe:.2f}")
        else:
            details.append(f"市盈率过高：{pe:.2f}")
        raw_score += pe_points
    else:
        details.append("净利润为零或负值，无法计算市盈率")

    # 2) 自由现金流比率（P/FCF）
    fcf_values = [getattr(fi, 'free_cash_flow', None) for fi in financial_line_items if hasattr(fi, 'free_cash_flow') and getattr(fi, 'free_cash_flow', None) is not None]
    recent_fcf = fcf_values[0] if fcf_values else None
    if recent_fcf and recent_fcf > 0:
        pfcf = market_cap / recent_fcf
        pfcf_points = 0
        if pfcf < 20:
            pfcf_points = 2
            details.append(f"自由现金流比率合理：{pfcf:.2f}")
        elif pfcf < 30:
            pfcf_points = 1
            details.append(f"自由现金流比率偏高：{pfcf:.2f}")
        else:
            details.append(f"自由现金流比率过高：{pfcf:.2f}")
        raw_score += pfcf_points
    else:
        details.append("自由现金流为零或负值，无法计算比率")

    # 转换为0-10分
    final_score = min(10, (raw_score / 4) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_insider_activity(insider_trades: list) -> dict:
    """
    评估内部交易活动：
    - 内部买入/卖出比例
    
    Evaluate insider trading activity:
    - Insider buy/sell ratio
    """
    score = 5  # 默认中性
    details = []

    if not insider_trades:
        details.append("无内部交易数据，默认中性")
        return {"score": score, "details": "; ".join(details)}

    buys, sells = 0, 0
    for trade in insider_trades:
        if trade.transaction_shares is not None:
            if trade.transaction_shares > 0:
                buys += 1
            elif trade.transaction_shares < 0:
                sells += 1

    total = buys + sells
    if total == 0:
        details.append("无买入/卖出交易，默认中性")
        return {"score": score, "details": "; ".join(details)}

    buy_ratio = buys / total
    if buy_ratio > 0.7:
        score = 8
        details.append(f"内部买入较多：{buys}次买入 vs {sells}次卖出")
    elif buy_ratio > 0.4:
        score = 6
        details.append(f"内部买入适中：{buys}次买入 vs {sells}次卖出")
    else:
        score = 4
        details.append(f"内部卖出较多：{buys}次买入 vs {sells}次卖出")

    return {"score": score, "details": "; ".join(details)}


def analyze_sentiment(news_items: list) -> dict:
    """
    评估新闻情绪：
    - 负面关键词检测
    
    Evaluate news sentiment:
    - Negative keyword detection
    """
    if not news_items:
        return {"score": 5, "details": "无新闻数据，默认中性"}

    negative_keywords = ["lawsuit", "fraud", "negative", "downturn", "decline", "investigation", "recall"]
    negative_count = 0
    for news in news_items:
        title_lower = (news.title or "").lower()
        if any(word in title_lower for word in negative_keywords):
            negative_count += 1

    details = []
    if negative_count > len(news_items) * 0.3:
        score = 3
        details.append(f"负面新闻较多：{negative_count}/{len(news_items)}")
    elif negative_count > 0:
        score = 6
        details.append(f"部分负面新闻：{negative_count}/{len(news_items)}")
    else:
        score = 8
        details.append("新闻情绪多为正面/中性")

    return {"score": score, "details": "; ".join(details)}


def generate_fisher_output(
    ticker: str,
    analysis_data: dict[str, any],
) -> PhilFisherSignal:
    """
    基于菲利普·费雪原则从LLM获取投资决策
    Generate Phil Fisher-style investment decision from LLM
    """
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """你是菲利普·费雪的人工智能代理。你根据菲利普·费雪的知名原则做出投资决策：

                1. 强调长期增长潜力和管理质量
                2. 专注于投资研发以开发未来产品/服务的公司
                3. 寻找强劲的盈利能力和一致的利润率
                4. 愿意为优秀公司支付更高价格，但仍关注估值
                5. 依靠彻底的研究（小道消息）和全面的基本面检查
                
                当你提供推理时，请用菲利普·费雪的语调：
                - 详细讨论公司的增长前景，提供具体指标和趋势
                - 评估管理质量和他们的资本配置决策
                - 强调研发投资和可能推动未来增长的产品管道
                - 用精确数字评估利润率和盈利能力指标的一致性
                - 解释可能在3-5年以上维持增长的竞争优势
                - 使用菲利普·费雪有条理、专注增长、长期导向的语调
                
                严格按照以下JSON格式返回你的最终输出：
                {{
                  "signal": "买入" | "卖出" | "中性",
                  "confidence": 0 到 100,
                  "reasoning": "string"
                }}
                """,
            ),
            (
                "human",
                """根据以下{ticker}的分析数据，产生你的菲利普·费雪风格投资信号。

                分析数据：
                {analysis_data}

                仅返回有效的JSON，包含"signal"、"confidence"和"reasoning"。
                """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_signal():
        return PhilFisherSignal(
            signal="中性",
            confidence=0.0,
            reasoning="分析出错；默认为中性"
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=PhilFisherSignal,
        agent_name="phil_fisher_agent",
        default_factory=create_default_signal,
    )
