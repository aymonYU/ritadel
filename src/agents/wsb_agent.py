"""
WallStreetBets风格投资分析代理
WallStreetBets-style Investment Analysis Agent

实现基于散户投资者心理和社交媒体热度的投资分析
Implements investment analysis based on retail investor psychology and social media hype
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
import json
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm
import praw
from datetime import datetime, timedelta
import os

from tools.api import get_financial_metrics, get_market_cap, search_line_items, get_company_news


class WSBSignal(BaseModel):
    """
    WSB分析信号模型 - 包含投资信号、置信度和推理
    WSB analysis signal model - Contains investment signal, confidence and reasoning
    """
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


class RedditPost(BaseModel):
    """
    Reddit帖子模型 - 存储WSB帖子的关键信息
    Reddit post model - Stores key information from WSB posts
    """
    title: str = Field(..., description="帖子标题 - Post title")
    score: int = Field(..., description="帖子分数 - Post score (upvotes)")
    num_comments: int = Field(..., description="评论数量 - Number of comments")
    created_utc: float = Field(..., description="发布时间戳 - Creation timestamp")
    url: str = Field(..., description="帖子链接 - Post URL")
    author: str = Field(..., description="作者 - Author")
    selftext: str = Field(default="", description="帖子内容 - Post content")
    sentiment: Literal["bullish", "bearish", "neutral"] = Field(default="neutral", description="情绪倾向 - Sentiment classification")


def wsb_agent(state: AgentState):
    """
    使用WallStreetBets风格指标分析股票：
    1. 分析meme潜力和社交媒体热度
    2. 识别空头挤压候选股票
    3. 期权链分析YOLO潜力
    4. 反向操作机构视角
    5. 基于动量的技术指标
    
    Analyzes stocks using WallStreetBets-style metrics:
    1. Meme potential and social media hype
    2. Short squeeze candidates
    3. Options chain analysis for YOLO potential
    4. Contrarian plays against institutional perspectives
    5. Momentum-based technical indicators
    """
    data = state["data"]
    end_date = data["end_date"]
    start_date = data.get("start_date")  # 可能为None - This might be None
    tickers = data["tickers"]
    
    # 存储分析数据 - Store analysis data
    analysis_data = {}
    wsb_analysis = {}
    
    for ticker in tickers:
        progress.update_status("wsb_agent", ticker, "Fetching financial metrics")
        # 获取所需数据 - Fetch required data
        metrics = get_financial_metrics(ticker, end_date, period="annual", limit=5)
        
        progress.update_status("wsb_agent", ticker, "Gathering financial line items")
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",  # 收入
                "net_income",  # 净利润
                "outstanding_shares",  # 流通股数
                "cash_and_equivalents",  # 现金及等价物
                "total_debt",  # 总债务
                "research_and_development",  # 研发费用
            ],
            end_date,
            period="annual",
            limit=5,
        )
        
        progress.update_status("wsb_agent", ticker, "Getting market cap")
        market_cap = get_market_cap(ticker, end_date)
        
        progress.update_status("wsb_agent", ticker, "Fetching Reddit WSB posts")
        # 获取少量高质量的最新Reddit帖子 - Get a small number of high-quality, recent Reddit posts
        print(f"\n--- FETCHING TOP RECENT WSB POSTS FOR ${ticker} ---\n")
        reddit_posts = get_reddit_posts(ticker, start_date, end_date, limit=10)
        
        progress.update_status("wsb_agent", ticker, "Analyzing social media hype")
        # 获取公司新闻来分析社交情绪 - Get company news to analyze social sentiment
        company_news = get_company_news(ticker, end_date, limit=100)
        
        progress.update_status("wsb_agent", ticker, "Analyzing meme potential")
        meme_analysis = analyze_meme_potential(company_news, ticker, market_cap, reddit_posts)
        
        progress.update_status("wsb_agent", ticker, "Identifying short squeeze potential")
        squeeze_analysis = analyze_short_squeeze_potential(metrics, financial_line_items, market_cap, ticker)
        
        progress.update_status("wsb_agent", ticker, "Analyzing YOLO options potential")
        options_analysis = analyze_options_potential(metrics, financial_line_items, market_cap)
        
        # 计算总分 - Calculate total score
        total_score = (
            meme_analysis["score"] + 
            squeeze_analysis["score"] + 
            options_analysis["score"]
        )
        max_possible_score = 15  # 将分数标准化为15分制 - Normalize scores to be out of 15
        
        # 基于WSB心理生成交易信号 - Generate trading signal based on WSB mentality
        if total_score >= 0.6 * max_possible_score:  # 较低的看涨阈值 - WSB乐观主义！ - Lower threshold for bullish - WSB is optimistic!
            signal = "bullish"
        elif total_score <= 0.3 * max_possible_score:
            signal = "bearish"
        else:
            signal = "neutral"
        
        # 存储分析数据 - Store analysis data
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "meme_analysis": meme_analysis,
            "squeeze_analysis": squeeze_analysis,
            "options_analysis": options_analysis,
            "market_cap": market_cap,
            "reddit_data": {
                "post_count": len(reddit_posts),
                "top_posts": [post.model_dump() for post in reddit_posts[:5]] if reddit_posts else []
            }
        }
        
        progress.update_status("wsb_agent", ticker, "Generating WSB-style analysis")
        wsb_output = generate_wsb_output(
            ticker=ticker,
            analysis_data=analysis_data,
            # model_name=state["metadata"]["model_name"], # 已移除，固定使用GPT-4o - Removed, fixed to use GPT-4o
            # model_provider=state["metadata"]["model_provider"], # 已移除，固定使用GPT-4o - Removed, fixed to use GPT-4o
        )
        
        # 以与其他代理一致的格式存储分析 - Store analysis in consistent format with other agents
        wsb_analysis[ticker] = {
            "signal": wsb_output.signal,
            "confidence": wsb_output.confidence,
            "reasoning": wsb_output.reasoning,
        }
        
        progress.update_status("wsb_agent", ticker, "Done")
        
        # 移除推荐功能，简化情绪总结 - Remove testimonial feature and simplified sentiment summary
        if reddit_posts:
            # 显示帖子的简单统计 - Display simple stats about the posts
            bullish_count = sum(1 for post in reddit_posts if post.sentiment == "bullish")
            bearish_count = sum(1 for post in reddit_posts if post.sentiment == "bearish")
            neutral_count = len(reddit_posts) - bullish_count - bearish_count
            
            print(f"\nWSB Stats for {ticker}: {len(reddit_posts)} posts found.")
            print(f"Sentiment: {bullish_count} bullish, {bearish_count} bearish, {neutral_count} neutral\n")
    
    # 创建消息 - Create the message
    message = HumanMessage(
        content=json.dumps(wsb_analysis),
        name="wsb_agent"
    )
    
    # 如果请求则显示推理 - Show reasoning if requested
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(wsb_analysis, "WallStreetBets Agent")
    
    # 将信号添加到analyst_signals列表 - Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["wsb_agent"] = wsb_analysis
    
    return {
        "messages": [message],
        "data": state["data"]
    }


def get_reddit_posts(ticker: str, start_date: str = None, end_date: str = None, limit: int = 10) -> list[RedditPost]:
    """
    从Reddit WallStreetBets获取指定股票的帖子
    Fetch Reddit posts about a specific ticker from WallStreetBets subreddit
    """
    try:
        # 从环境变量获取Reddit API凭证 - Get Reddit API credentials from environment variables
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="WSB Investment Analysis Bot 1.0"
        )
        
        subreddit = reddit.subreddit("wallstreetbets")
        
        # 计算时间范围 - Calculate time range
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
            
        # 默认回溯7天 - Default to 7 days back
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = end_dt - timedelta(days=7)
        
        # 转换为时间戳 - Convert to timestamps
        start_timestamp = start_dt.timestamp()
        end_timestamp = end_dt.timestamp()
        one_day_ago = end_timestamp - 86400  # 24小时前 - 24 hours ago
        
        # 搜索相关的帖子 - Search for relevant posts
        # 搜索标题或内容中包含股票代码的帖子 - Search posts with ticker in title or text
        search_terms = [f"${ticker}", ticker.upper(), ticker.lower()]
        all_posts = []
        
        # 尝试多个搜索策略 - Try multiple search strategies
        try:
            # 策略1：搜索热门帖子 - Strategy 1: Search hot posts
            for submission in subreddit.hot(limit=1000):
                if submission.created_utc < start_timestamp or submission.created_utc > end_timestamp:
                    continue
                    
                title_text = submission.title.lower()
                if any(term.lower() in title_text for term in search_terms):
                    # 分析情绪 - Analyze sentiment
                    sentiment = analyze_post_sentiment(submission.title, submission.selftext)
                    
                    post = RedditPost(
                        title=submission.title,
                        score=submission.score,
                        num_comments=submission.num_comments,
                        created_utc=submission.created_utc,
                        url=submission.url,
                        author=str(submission.author),
                        selftext=submission.selftext[:500],  # 限制文本长度 - Limit text length
                        sentiment=sentiment
                    )
                    all_posts.append(post)
                    
                    if len(all_posts) >= limit * 3:  # 获取更多以便排序 - Get more for sorting
                        break
            
            # 策略2：搜索新帖子 - Strategy 2: Search new posts
            for submission in subreddit.new(limit=500):
                if submission.created_utc < start_timestamp or submission.created_utc > end_timestamp:
                    continue
                    
                title_text = submission.title.lower()
                if any(term.lower() in title_text for term in search_terms):
                    # 检查是否已存在 - Check if already exists
                    if not any(p.url == submission.url for p in all_posts):
                        sentiment = analyze_post_sentiment(submission.title, submission.selftext)
                        
                        post = RedditPost(
                            title=submission.title,
                            score=submission.score,
                            num_comments=submission.num_comments,
                            created_utc=submission.created_utc,
                            url=submission.url,
                            author=str(submission.author),
                            selftext=submission.selftext[:500],
                            sentiment=sentiment
                        )
                        all_posts.append(post)
                        
                        if len(all_posts) >= limit * 3:
                            break
                            
        except Exception as search_error:
            print(f"Error during Reddit search: {str(search_error)}")
        
        # 按相关性和时效性排序 - Sort by relevance and recency
        all_posts.sort(key=lambda x: (
            # 对过去24小时的帖子给予更高权重 - Higher weight to posts from the last 24 hours
            (2 if x.created_utc > one_day_ago else 1) * 0.7 +
            # 对帖子分数给予一定权重 - Some weight to post score
            (min(x.score, 1000) / 1000) * 0.3
        ), reverse=True)
        
        # 返回前几个帖子（限制到请求数量）- Return the top posts (limited to requested amount)
        return all_posts[:limit]
    
    except Exception as e:
        print(f"Error fetching Reddit data: {str(e)}")
        return []


def analyze_post_sentiment(title: str, text: str) -> str:
    """
    分析Reddit帖子的情绪倾向
    Analyze the sentiment of a Reddit post
    """
    # 看涨关键词 - Bullish keywords
    bullish_keywords = [
        "moon", "rocket", "buy", "calls", "bullish", "hold", "diamond hands", 
        "to the moon", "gains", "pump", "squeeze", "rally", "breakout"
    ]
    
    # 看跌关键词 - Bearish keywords
    bearish_keywords = [
        "puts", "short", "crash", "dump", "bearish", "sell", "drop", 
        "fall", "decline", "loss", "paper hands", "bag holder"
    ]
    
    combined_text = (title + " " + text).lower()
    
    bullish_count = sum(1 for keyword in bullish_keywords if keyword in combined_text)
    bearish_count = sum(1 for keyword in bearish_keywords if keyword in combined_text)
    
    if bullish_count > bearish_count:
        return "bullish"
    elif bearish_count > bullish_count:
        return "bearish"
    else:
        return "neutral"


def analyze_meme_potential(company_news: list, ticker: str, market_cap: float, reddit_posts: list[RedditPost] = None) -> dict:
    """
    分析股票作为meme股的潜力
    Analyze a stock's potential as a meme stock.
    
    分析因素：
    - 社交媒体热度/提及次数
    - 股价波动性
    - 品牌知名度和故事潜力
    - 市值（小到中盘股优先）
    - 叙事潜力（颠覆性、空头挤压等）
    - Reddit活跃度（帖子数量、情绪、参与度）
    
    Factors:
    - Social media buzz/mentions
    - Stock price volatility
    - Brand recognition and story potential
    - Market cap (small to mid-cap preferred)
    - Narrative potential (disruption, short squeeze, etc.)
    - Reddit activity (post volume, sentiment, engagement)
    """
    score = 0
    details = []
    
    # 检查新闻中的社交媒体提及 - Check for social media mentions in news
    social_keywords = [
        'reddit', 'twitter', 'wallstreetbets', 'wsb', 'social media', 'viral',
        'meme', 'trending', 'retail investors', 'robinhood', 'tiktok', 'hype',
        'discord', 'influencer', 'short sellers', 'squeeze'
    ]
    
    social_mentions = 0
    for news in company_news:
        title_lower = news.title.lower()
        for keyword in social_keywords:
            if keyword in title_lower:
                social_mentions += 1
                break
    
    # 基于社交媒体提及评分 - Score based on social mentions
    if social_mentions > 10:
        score += 5
        details.append(f"Major social media buzz: {social_mentions} mentions - peak meme potential")
    elif social_mentions > 5:
        score += 3
        details.append(f"Moderate social media presence: {social_mentions} mentions - gaining traction")
    elif social_mentions > 2:
        score += 1
        details.append(f"Some social media activity: {social_mentions} mentions - on the radar")
    else:
        details.append("Limited social media mentions - no meme buzz detected")
    
    # Reddit活跃度分析 - Reddit activity analysis
    if reddit_posts:
        # 按情绪统计帖子 - Count posts by sentiment
        bullish_posts = sum(1 for post in reddit_posts if post.sentiment == "bullish")
        bearish_posts = sum(1 for post in reddit_posts if post.sentiment == "bearish")
        
        # 总参与度（点赞+评论）- Total engagement (upvotes + comments)
        total_engagement = sum(post.score + post.num_comments for post in reddit_posts)
        avg_engagement = total_engagement / len(reddit_posts) if reddit_posts else 0
        
        # 计算Reddit评分组件 - Calculate Reddit score component
        reddit_score = 0
        
        # 帖子数量评分 - Post volume scoring
        if len(reddit_posts) > 20:
            reddit_score += 2
            details.append(f"Massive Reddit activity: {len(reddit_posts)} recent posts - viral meme status")
        elif len(reddit_posts) > 10:
            reddit_score += 1.5
            details.append(f"Strong Reddit activity: {len(reddit_posts)} recent posts - high meme potential")
        elif len(reddit_posts) > 5:
            reddit_score += 1
            details.append(f"Moderate Reddit activity: {len(reddit_posts)} recent posts - growing meme interest")
        elif len(reddit_posts) > 0:
            reddit_score += 0.5
            details.append(f"Some Reddit activity: {len(reddit_posts)} recent posts - on WSB radar")
        
        # 情绪评分（WSB喜欢积极性）- Sentiment scoring (WSB loves positivity)
        sentiment_ratio = bullish_posts / len(reddit_posts) if reddit_posts else 0
        if sentiment_ratio > 0.8:
            reddit_score += 1.5
            details.append(f"Overwhelmingly bullish Reddit sentiment: {sentiment_ratio:.0%} positive posts - rocket emoji territory")
        elif sentiment_ratio > 0.6:
            reddit_score += 1
            details.append(f"Bullish Reddit sentiment: {sentiment_ratio:.0%} positive posts - gaining ape followers")
        
        # 参与度评分 - Engagement scoring
        if avg_engagement > 1000:
            reddit_score += 1.5
            details.append(f"Massive Reddit engagement: {avg_engagement:.0f} avg upvotes+comments - peak meme energy")
        elif avg_engagement > 500:
            reddit_score += 1
            details.append(f"High Reddit engagement: {avg_engagement:.0f} avg upvotes+comments - strong meme potential")
        elif avg_engagement > 100:
            reddit_score += 0.5
            details.append(f"Decent Reddit engagement: {avg_engagement:.0f} avg upvotes+comments - respectable attention")
        
        score += min(reddit_score, 5)  # Reddit评分上限为5分 - Cap Reddit score at 5 points
    
    # meme潜力的市值分析 - Market cap analysis for meme potential
    # WSB倾向于选择他们实际能推动的股票 - 小到中盘股 - WSB tends to prefer stocks they can actually move - small to mid cap
    if market_cap:
        if 100_000_000 <= market_cap <= 10_000_000_000:  # $100M到$10B - $100M to $10B
            score += 3
            details.append(f"Perfect market cap for memes: ${market_cap/1_000_000_000:.1f}B - small enough to move")
        elif market_cap < 100_000_000:  # < $100M
            score += 2
            details.append(f"Micro-cap: ${market_cap/1_000_000:.1f}M - moonshot potential but super risky")
        elif market_cap <= 50_000_000_000:  # < $50B
            score += 1
            details.append(f"Mid-cap: ${market_cap/1_000_000_000:.1f}B - still movable with enough retail interest")
        else:
            details.append(f"Too large: ${market_cap/1_000_000_000:.1f}B - hard for retail to influence")
    
    # 股票代码分析 - 越短越适合meme - Ticker symbol analysis - shorter is better for memes
    if len(ticker) <= 3:
        score += 2
        details.append(f"Short, catchy ticker: ${ticker} - perfect for memes")
    elif len(ticker) == 4:
        score += 1
        details.append(f"Decent ticker length: ${ticker} - workable for memes")
    
    # 检查公司名称或新闻提及的品牌知名度 - Check for brand recognition from company name or news mentions
    brand_score = 0
    
    # Special cases for well-known meme stocks
    if ticker in ["GME", "AMC", "BB", "PLTR", "TSLA", "HOOD", "BBBY", "NOK", "WISH", "CLOV"]:
        brand_score = 5
        details.append(f"Classic meme stock: ${ticker} - proven retail favorite")
    else:
        # Extract company name from news if available
        company_names = set([news.title.split(':')[0] for news in company_news[:5] if ':' in news.title])
        
        if len(company_names) > 0:
            brand_score = min(3, len(company_names))
            details.append(f"Some brand recognition: mentioned across {len(company_names)} sources")
    
    score += brand_score
    
    reddit_stats = {
        "post_count": len(reddit_posts) if reddit_posts else 0,
        "bullish_count": bullish_posts if 'bullish_posts' in locals() else 0,
        "bearish_count": bearish_posts if 'bearish_posts' in locals() else 0,
        "avg_engagement": avg_engagement if 'avg_engagement' in locals() else 0
    }
    
    return {
        "score": min(score, 10) / 2,  # Normalize to 0-5 scale
        "details": "; ".join(details),
        "social_mentions": social_mentions,
        "brand_score": brand_score,
        "reddit_stats": reddit_stats
    }


def analyze_short_squeeze_potential(metrics: list, financial_line_items: list, market_cap: float, ticker: str) -> dict:
    """
    分析空头挤压的潜力
    Analyze potential for a short squeeze.
    
    分析因素：
    - 空头利率比例（越高越有利于挤压）
    - 覆盖天数（越高越有利于挤压）
    - 流通股规模（越小越好）
    - 近期价格动量
    - 机构与散户持股比例
    
    Factors:
    - Short interest ratio (higher is better for a squeeze)
    - Days to cover (higher is better for a squeeze)
    - Float size (smaller is better)
    - Recent price momentum
    - Institutional vs. retail ownership
    """
    score = 0
    details = []
    
    # 对于真实实现，您需要从API获取空头利率数据 - For a real implementation, you would pull short interest data from an API
    # 这里我们基于可用指标进行模拟 - Here we'll simulate it based on available metrics
    
    if not metrics or not financial_line_items:
        return {
            "score": 0,
            "details": "Insufficient data to analyze short squeeze potential"
        }
    
    # 检查价格波动性 - 这是挤压的先决条件 - Check for price volatility - a prerequisite for a squeeze
    # 在真实实现中，您需要计算实际波动性 - In a real implementation, you'd calculate the actual volatility
    if len(metrics) >= 2:
        # 模拟高债务低现金股票的高波动性 - Simulate high volatility for stocks with high debt and low cash
        latest = financial_line_items[0]
        if hasattr(latest, 'cash_and_equivalents') and hasattr(latest, 'total_debt'):
            if latest.cash_and_equivalents and latest.total_debt:
                cash_to_debt = latest.cash_and_equivalents / latest.total_debt if latest.total_debt > 0 else float('inf')
                if cash_to_debt < 0.3:
                    score += 2
                    details.append("High cash/debt pressure - boosts squeeze potential")
                elif cash_to_debt < 0.7:
                    score += 1
                    details.append("Moderate cash/debt pressure - some squeeze potential")
    
    # 基于市值和财务数据估算流通股 - Estimated float based on market cap and financial data
    float_score = 0
    if market_cap and financial_line_items[0].outstanding_shares:
        shares = financial_line_items[0].outstanding_shares
        avg_price = market_cap / shares
        
        # 小流通股更适合挤压 - Small float is better for squeezes
        if shares < 50_000_000:
            float_score = 3
            details.append(f"Small float ({shares/1_000_000:.1f}M shares) - perfect for a squeeze!")
        elif shares < 200_000_000:
            float_score = 2
            details.append(f"Medium float ({shares/1_000_000:.1f}M shares) - decent squeeze potential")
        elif shares < 500_000_000:
            float_score = 1
            details.append(f"Large float ({shares/1_000_000:.1f}M shares) - harder to squeeze but possible")
        else:
            details.append(f"Huge float ({shares/1_000_000:.1f}M shares) - would take massive volume to squeeze")
    
    score += float_score
    
    # 盈利能力因子 - 无盈利公司通常有更高的空头利率 - Profitability factor - unprofitable companies often have higher short interest
    profit_score = 0
    if len(financial_line_items) >= 2:
        recent_profits = [item.net_income for item in financial_line_items[:2] if hasattr(item, 'net_income') and item.net_income is not None]
        if recent_profits and all(profit < 0 for profit in recent_profits):
            profit_score = 3
            details.append("Consistently unprofitable - likely high short interest")
        elif recent_profits and any(profit < 0 for profit in recent_profits):
            profit_score = 2
            details.append("Mixed profitability - moderate short interest likely")
    
    score += profit_score
    
    # 行业因子 - 某些行业更容易发生空头挤压 - Industry factor - some industries are more prone to short squeezes
    # 使用真实行业分类数据会更好 - This would be better with real industry classification data
    industry_score = 0
    if ticker.startswith(('GME', 'AMC', 'BB', 'NOK')):  # 传统科技或娱乐 - Legacy tech or entertainment
        industry_score = 2
        details.append("Industry with historical squeeze precedent")
    elif ticker.startswith(('TSLA', 'LCID', 'RIVN')):  # 电动汽车板块 - EV sector
        industry_score = 2
        details.append("EV sector with high short interest history")
    elif ticker.startswith(('PLTR', 'AI', 'PATH')):  # 科技/AI - Tech/AI
        industry_score = 1
        details.append("Tech sector with moderate short interest potential")
    
    score += industry_score
    
    return {
        "score": min(score, 10) / 2,  # 标准化为0-5分制 - Normalize to 0-5 scale
        "details": "; ".join(details),
        "float_score": float_score,
        "profit_score": profit_score,
        "industry_score": industry_score
    }


def analyze_options_potential(metrics: list, financial_line_items: list, market_cap: float) -> dict:
    """
    分析股票在WSB流行的期权交易策略中的潜力
    Analyze a stock's potential for options trading strategies popular on WSB.
    
    分析因素：
    - 价格波动性（越高期权越有利）
    - 期权链流动性（估算）
    - 价格点（不能太低，也不能太高）
    - 新闻或事件催化剂潜力
    - 盈利惊喜历史
    
    Factors:
    - Price volatility (higher is better for options)
    - Options chain liquidity (estimated)
    - Price point (not too low, not too high)
    - Catalyst potential from news or events
    - Earnings surprise history
    """
    score = 0
    details = []
    
    if not metrics or not financial_line_items or not market_cap:
        return {
            "score": 0,
            "details": "Insufficient data for options analysis"
        }
    
    # 计算股价（市值/流通股数）- Calculate share price (market cap / outstanding shares)
    share_price = 0
    if financial_line_items[0].outstanding_shares and financial_line_items[0].outstanding_shares > 0:
        share_price = market_cap / financial_line_items[0].outstanding_shares
    
    # 分析期权流动性的价格点 - Analyze price point for options liquidity
    price_score = 0
    if 10 <= share_price <= 500:
        price_score = 3
        details.append(f"Perfect price range for options: ${share_price:.2f} - liquid chains")
    elif 5 <= share_price < 10:
        price_score = 2
        details.append(f"Affordable options but less liquid: ${share_price:.2f}")
    elif 500 < share_price <= 1000:
        price_score = 2
        details.append(f"High-priced options: ${share_price:.2f} - expensive premiums but good leverage")
    elif share_price > 1000:
        price_score = 1
        details.append(f"Very expensive options: ${share_price:.2f} - may need spreads")
    elif share_price > 0:
        price_score = 1
        details.append(f"Too cheap for good options: ${share_price:.2f} - penny stock territory")
    
    score += price_score
    
    # 分析波动性潜力（真实实现中，使用实际波动性指标）- Analyze volatility potential (for real implementation, use actual volatility metrics)
    vol_score = 0
    if len(metrics) >= 2:
        # 如果市盈率为负或极高，通常表示波动性 - If price-to-earnings ratio is negative or extremely high, that often indicates volatility
        pe_ratio = metrics[0].price_to_earnings_ratio
        if pe_ratio is not None and (pe_ratio < 0 or pe_ratio > 100):
            vol_score = 3
            details.append(f"High expected volatility: P/E ratio {pe_ratio:.1f}")
        elif pe_ratio is not None and pe_ratio > 50:
            vol_score = 2
            details.append(f"Moderate expected volatility: P/E ratio {pe_ratio:.1f}")
        elif pe_ratio is not None:
            vol_score = 1
            details.append(f"Lower expected volatility: P/E ratio {pe_ratio:.1f}")
    
    score += vol_score
    
    # 分析期权流动性的市值 - Analyze market cap for options liquidity
    mcap_score = 0
    if market_cap > 10_000_000_000:  # > $10B
        mcap_score = 3
        details.append(f"Large cap (${market_cap/1_000_000_000:.1f}B) - liquid options market")
    elif market_cap > 2_000_000_000:  # > $2B
        mcap_score = 2
        details.append(f"Mid cap (${market_cap/1_000_000_000:.1f}B) - decent options liquidity")
    elif market_cap > 300_000_000:  # > $300M
        mcap_score = 1
        details.append(f"Small cap (${market_cap/1_000_000:.1f}M) - limited options liquidity")
    else:
        details.append(f"Micro cap (${market_cap/1_000_000:.1f}M) - poor options liquidity")
    
    score += mcap_score
    
    # WSB风格期权玩法的额外因子 - Additional factors for WSB-style options plays
    if financial_line_items[0].research_and_development and financial_line_items[0].revenue:
        # 检查研发投入相对于收入是否较高（科技/生物技术在WSB很流行）- Check if R&D is high relative to revenue (tech/biotech plays popular on WSB)
        rd_to_revenue = financial_line_items[0].research_and_development / financial_line_items[0].revenue
        if rd_to_revenue > 0.2:  # >20% of revenue on R&D
            score += 1
            details.append(f"High R&D spending ({rd_to_revenue:.1%} of revenue) - potential for binary events")
    
    return {
        "score": min(score, 10) / 2,  # 标准化为0-5分制 - Normalize to 0-5 scale
        "details": "; ".join(details),
        "price": share_price,
        "price_score": price_score,
        "volatility_score": vol_score,
        "market_cap_score": mcap_score
    }


# 移除了model_name和model_provider参数，因为模型固定为GPT-4o - Removed model_name and model_provider parameters as the model is fixed to GPT-4o
def generate_wsb_output(
    ticker: str,
    analysis_data: dict[str, any],
    # model_name: str, # 已移除 (Removed)
    # model_provider: str, # 已移除 (Removed)
) -> WSBSignal:
    """
    从LLM生成WSB风格的投资决策
    Generate WSB-style investment decision from LLM.
    """
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert WallStreetBets trader. You analyze stocks based on retail trader psychology and social media sentiment:

            1. Identify meme stock potential and viral social media trends
            2. Find short squeeze opportunities based on technical indicators
            3. Evaluate YOLO options plays for maximum leverage potential
            4. Use retail trader hype and momentum indicators
            5. Consider contrarian positions against institutional wisdom
            
            Key trading philosophy:
            - Diamond hands > paper hands (hold strong positions)
            - Look for asymmetric risk/reward (high potential upside)
            - Social media buzz and retail sentiment drive prices
            - Options chains and gamma squeezes create explosive moves
            - "This is the way" - follow the crowd when momentum is building
            
            Your analysis should be energetic, optimistic when bullish, and use WSB terminology naturally. Focus on actionable trades that could generate significant returns.
            """
        ),
        (
            "human",
            """Based on the following WSB-style analysis, create an investment signal:

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

    # 为WSBSignal创建默认工厂 - Create default factory for WSBSignal
    def create_default_signal():
        return WSBSignal(signal="neutral", confidence=0.0, reasoning="Error in analysis, defaulting to neutral")

    # 调用call_llm时不再传递model_name和model_provider - model_name and model_provider are no longer passed when calling call_llm
    return call_llm(
        prompt=prompt,
        # model_name=model_name, # 已移除 (Removed)
        # model_provider=model_provider, # 已移除 (Removed)
        pydantic_model=WSBSignal,
        agent_name="wsb_agent",
        default_factory=create_default_signal,
    ) 