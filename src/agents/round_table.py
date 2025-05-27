"""
投资圆桌讨论代理 - 分析师协作决策系统
Investment Round Table Agent - Analyst collaborative decision system

模拟投资分析师圆桌讨论，综合各种分析信号形成最终投资决策
Simulates investment analyst round table discussions to synthesize various analytical signals into final investment decisions
"""
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
import json
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm
from colorama import Fore, Style

class RoundTableOutput(BaseModel):
    """圆桌讨论输出模型 - Round table discussion output model"""
    signal: Literal["bullish", "bearish", "neutral"] = Field(description="投资信号：看涨/看跌/中性 - Investment signal: bullish/bearish/neutral")
    confidence: float = Field(description="0到100之间的置信度 - Confidence level between 0 and 100")
    reasoning: str = Field(description="决策背后的详细推理 - Detailed reasoning behind the decision")
    discussion_summary: str = Field(description="讨论要点摘要 - Summary of the key points from the discussion")
    consensus_view: str = Field(description="达成的主要共识观点 - The main consensus view that emerged")
    dissenting_opinions: str = Field(description="值得注意的反对观点 - Notable contrarian perspectives")
    conversation_transcript: str = Field(description="模拟对话的记录 - Transcript of the simulated conversation")


def round_table(data, model_name, model_provider, show_reasoning=True):
    """
    基于分析师信号模拟投资分析师之间的圆桌讨论
    
    这是一个独立功能，通过模拟对话将各种代理的分析
    综合成全面的投资决策。
    
    Simulates a round table discussion among investment analysts based on their signals.
    
    This is a standalone feature that synthesizes the analysis of various agents
    into a comprehensive investment decision through simulated dialogue.
    
    Args:
        data: 包含分析师信号和股票信息的字典 - Dictionary containing analyst signals and ticker information
        model_name: 要使用的LLM模型名称 - Name of the LLM model to use
        model_provider: LLM模型提供商 - Provider of the LLM model
        show_reasoning: 是否打印详细对话 - Whether to print the detailed conversation
        
    Returns:
        每个股票的圆桌讨论决策字典 - Dictionary containing the round table decision for each ticker
    """
    print(f"\n{Fore.CYAN}{Style.BRIGHT}投资圆桌讨论 - Investment Round Table Discussion{Style.RESET_ALL}")
    
    analyst_signals = data.get("analyst_signals", {})
    tickers = data.get("tickers", [])
    
    if not analyst_signals:
        print(f"{Fore.RED}圆桌讨论无可用分析师信号 - No analyst signals available for round table discussion{Style.RESET_ALL}")
        return {}
    
    print(f"可用信号来自：{list(analyst_signals.keys())} - Available signals from: {list(analyst_signals.keys())}")
    
    # 跳过风险管理和投资组合管理信号 - Skip risk management and portfolio management signals
    filtered_signals = {
        agent: signals for agent, signals in analyst_signals.items() 
        if agent not in ["risk_management_agent", "master_agent", "round_table_agent"]
    }
    
    # 为每个股票代码初始化圆桌分析 - Initialize round table analysis for each ticker
    round_table_analysis = {}
    
    for ticker in tickers:
        progress.update_status("round_table", ticker, "Collecting analyst inputs")
        
        # 收集该股票的所有个别代理信号 - Collect all individual agent signals for this ticker
        ticker_signals = {}
        for agent_name, signals in filtered_signals.items():
            if ticker in signals:
                ticker_signals[agent_name] = signals[ticker]
        
        if not ticker_signals:
            progress.update_status("round_table", ticker, "No signals found for discussion")
            print(f"{Fore.RED}未找到{ticker}的分析师信号。无法进行圆桌讨论。- No analyst signals found for {ticker}. Cannot conduct round table.{Style.RESET_ALL}")
            continue
        
        print(f"{Fore.CYAN}为{ticker}找到{len(ticker_signals)}个分析师信号 - Found {len(ticker_signals)} analyst signals for {ticker}{Style.RESET_ALL}")
        progress.update_status("round_table", ticker, f"Simulating discussion with {len(ticker_signals)} analysts")
        
        # 模拟圆桌讨论 - Simulate the round table discussion
        round_table_output = simulate_round_table(
            ticker=ticker,
            ticker_signals=ticker_signals,
            model_name=model_name,
            model_provider=model_provider,
        )
        
        # 存储分析结果 - Store analysis
        round_table_analysis[ticker] = {
            "signal": round_table_output.signal,
            "confidence": round_table_output.confidence,
            "reasoning": round_table_output.reasoning,
            "discussion_summary": round_table_output.discussion_summary,
            "consensus_view": round_table_output.consensus_view,
            "dissenting_opinions": round_table_output.dissenting_opinions,
            "conversation_transcript": round_table_output.conversation_transcript
        }
        
        # 总是打印标题以显示我们正在运行 - Always print the header to show we're running
        print(f"\n{Fore.WHITE}{Style.BRIGHT}===== 投资圆桌讨论 - INVESTMENT ROUND TABLE: {Fore.CYAN}{ticker}{Fore.WHITE} ====={Style.RESET_ALL}")
        
        # 以可读格式打印对话记录 - Print the conversation transcript in a readable format
        if show_reasoning:
            print_readable_conversation(round_table_output.conversation_transcript)
            print(f"\n{Fore.WHITE}{Style.BRIGHT}===== 结论 - CONCLUSION ====={Style.RESET_ALL}")
            print(f"{Fore.YELLOW}信号 - Signal: {get_signal_color(round_table_output.signal)}{round_table_output.signal.upper()}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}置信度 - Confidence: {Fore.WHITE}{round_table_output.confidence}%{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}推理 - Reasoning: {Fore.WHITE}{round_table_output.reasoning}{Style.RESET_ALL}\n")
        else:
            # 如果show_reasoning关闭，只打印摘要 - Print just a summary if show_reasoning is off
            transcript_preview = round_table_output.conversation_transcript.split('\n')[:5]
            print('\n'.join(transcript_preview))
            print(f"{Fore.YELLOW}... [设置--show-reasoning查看完整对话 - Set --show-reasoning to see full conversation] ...{Style.RESET_ALL}")
            
        print(f"{Fore.WHITE}{Style.BRIGHT}{'=' * 80}{Style.RESET_ALL}\n")
        progress.update_status("round_table", ticker, "Discussion completed")
    
    # 如果需要，显示综合分析 - Display the comprehensive analysis if requested
    if show_reasoning:
        show_agent_reasoning(round_table_analysis, "Investment Round Table")
    
    return round_table_analysis


def print_readable_conversation(transcript: str):
    """
    以更易读的方式格式化和打印对话，使用颜色编码
    Format and print the conversation in a more readable way with color coding.
    """
    lines = transcript.split('\n')
    
    # 为不同分析师定义颜色 - Define colors for different analysts
    analyst_colors = {
        "Warren Buffett": Fore.GREEN,     # 沃伦·巴菲特
        "Charlie Munger": Fore.GREEN + Style.BRIGHT,  # 查理·芒格
        "Ben Graham": Fore.GREEN,         # 本杰明·格雷厄姆
        "Cathie Wood": Fore.MAGENTA,      # 凯茜·伍德
        "Bill Ackman": Fore.BLUE + Style.BRIGHT,      # 比尔·阿克曼
        "Nancy Pelosi": Fore.CYAN,        # 南希·佩洛西
        "Technical Analyst": Fore.YELLOW, # 技术分析师
        "Fundamental Analyst": Fore.WHITE + Style.BRIGHT,  # 基本面分析师
        "Sentiment Analyst": Fore.RED,    # 情绪分析师
        "Valuation Analyst": Fore.BLUE,   # 估值分析师
        "WSB": Fore.RED + Style.BRIGHT,   # WSB分析师
        "Moderator": Fore.WHITE,          # 主持人
    }
    
    current_analyst = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检查这一行是否开始新的发言者 - Check if this line starts a new speaker
        for analyst in analyst_colors:
            if line.startswith(f"{analyst}:") or line.startswith(f"**{analyst}:**"):
                current_analyst = analyst
                # 格式：分析师名称用颜色，然后是消息 - Format: Analyst name in color, then the message
                name_end = line.find(':') + 1
                print(f"{analyst_colors[analyst]}{line[:name_end]}{Style.RESET_ALL}{line[name_end:]}")
                break
        else:
            # 前一发言者的继续或一般文本 - Continuation of previous speaker or general text
            if current_analyst and not any(marker in line for marker in ['===', '---', '***']):
                print(f"  {line}")
            else:
                # 章节标题或其他格式 - Section headers or other formatting
                print(f"{Fore.WHITE}{Style.BRIGHT}{line}{Style.RESET_ALL}")


def get_signal_color(signal: str) -> str:
    """
    为信号返回适当的颜色
    Return the appropriate color for a signal
    """
    if signal.lower() == "bullish":
        return Fore.GREEN     # 看涨 - 绿色
    elif signal.lower() == "bearish":
        return Fore.RED       # 看跌 - 红色
    else:
        return Fore.YELLOW    # 中性 - 黄色


def simulate_round_table(
    ticker: str,
    ticker_signals: dict[str, any],
    model_name: str,
    model_provider: str,
) -> RoundTableOutput:
    """
    模拟分析师之间的圆桌讨论并达成决策
    Simulate a round table discussion among analysts and reach a decision.
    """
    template = ChatPromptTemplate.from_messages([
        (
            "system",
            """你是投资圆桌讨论的主持人，各种金融分析师在此讨论投资决策。设计一个逻辑性强、自然的对话，其中：

            1. 每个分析师只有在有价值的贡献时才发言
            2. 讨论像真实会议一样自然流动，而不是脚本化的轮流发言
            3. 分析师在相关时直接回应其他人提出的观点
            4. 分歧点会被自然地探讨直至解决
            5. 对话持续到达成充分理由的决策
            6. 没有人为的轮流发言或强制贡献

            关键要求：
            - 简洁：每个陈述都应该直接而切中要点
            - 逻辑性：对话应该遵循自然的思想流程
            - 无废话：严格削减任何行话、冗余或不必要的解释
            - 无脚本：不要强迫每个分析师发言 - 只在他们有有用见解时
            - 真实分歧：允许分析师直接挑战彼此
            - 自然解决：让共识从讨论中自然涌现
            - 完整分析：继续直到考虑了所有重要方面
            
            You are the moderator of an Investment Round Table where various financial analysts 
            discuss an investment decision. Design a logical, natural conversation where:

            1. Each analyst only speaks when they have something valuable to contribute
            2. The discussion flows organically like a real meeting, not a scripted round-robin
            3. Analysts respond directly to points made by others when relevant
            4. Points of disagreement are naturally explored until resolution
            5. The conversation continues until a well-reasoned decision is reached
            6. No artificial turn-taking or forced contributions

            Key requirements:
            - CONCISE: Every statement should be direct and to the point
            - LOGICAL: The conversation should follow a natural flow of ideas
            - NO BS: Cut ruthlessly any jargon, fluff, or unnecessary explanation
            - NO SCRIPT: Don't force every analyst to speak - only when they have something useful to say
            - REAL DISAGREEMENT: Allow analysts to challenge each other directly
            - NATURAL RESOLUTION: Let the consensus emerge organically from the discourse
            - COMPLETE ANALYSIS: Continue until all important aspects have been considered

            Analyst Personas (maintain authentic personalities):
            - Warren Buffett: Patient, folksy but incisive, focused on business fundamentals
            - Charlie Munger: Blunt, no-nonsense, critical of foolishness, mental models
            - Ben Graham: Conservative, risk-averse, values margin of safety above all
            - Cathie Wood: Bold, disruptive-tech enthusiast, future-focused, dismissive of old metrics
            - Bill Ackman: Forceful, activist mindset, confident in strong opinions
            - Nancy Pelosi: Political insider, pragmatic, focused on policy impacts
            - Technical Analyst: Pattern-focused, dismissive of fundamentals when trends are clear
            - Fundamental Analyst: By-the-numbers, methodical, skeptical of hype
            - Sentiment Analyst: Attuned to market psychology and news flow
            - Valuation Analyst: Focused on price vs. value, multiple-based comparisons
            - WSB (WallStreetBets): Irreverent, momentum-driven, contrarian, slang-heavy

            Format the conversation naturally:
            - Each speaker clearly labeled (e.g., "Warren Buffett: I believe...")
            - Direct statements, no meandering explanations
            - Natural interruptions and crosstalk when appropriate
            - Minimal moderator interventions - let the discussion flow
            - Strong opinions clearly expressed
            """
        ),
        (
            "human",
            """Facilitate a realistic Investment Round Table discussion about {ticker} with the following analyst signals:

            Analyst Signals and Reasoning:
            {ticker_signals}

            Create a logical discussion flow where each analyst speaks ONLY when they have something valuable 
            to add. Allow the conversation to continue until all important aspects have been thoroughly 
            explored and a well-reasoned decision is reached.

            Guidelines:
            - Let the conversation flow NATURALLY - analysts should respond to each other directly
            - Keep each contribution CONCISE and TO THE POINT
            - Allow DISAGREEMENT to play out fully with direct challenges
            - Don't artificially include everyone - some may contribute more than others
            - Let discussion continue until a TRUE CONSENSUS emerges (or clear disagreement is documented)
            - Focus on getting to the RIGHT ANSWER, not a specific format or length

            IMPORTANT FORMAT INSTRUCTIONS:
            Your response must be a valid JSON object with these fields:
            - signal: "bullish" or "bearish" or "neutral" string
            - confidence: a number between 0-100
            - reasoning: a string explaining the final decision
            - discussion_summary: a string summarizing key points
            - consensus_view: a string describing areas of agreement
            - dissenting_opinions: a string summarizing contrarian views
            - conversation_transcript: a STRING (not an array/list) containing the complete conversation

            For the conversation_transcript, combine all dialogue into a SINGLE STRING with line breaks.
            DO NOT format it as an array or list of messages.

            Example of proper JSON format:
            {{
              "signal": "bullish",
              "confidence": 75,
              "reasoning": "Based on strong growth and valuation...",
              "discussion_summary": "The committee focused on...",
              "consensus_view": "Most analysts agreed that...",
              "dissenting_opinions": "Charlie Munger disagreed with...",
              "conversation_transcript": "Moderator: Welcome everyone...\\nWarren Buffett: I've looked at...\\nCathie Wood: The innovation potential..."
            }}
            """
        )
    ])

    # Generate the prompt
    prompt = template.invoke({
        "ticker_signals": json.dumps(ticker_signals, indent=2),
        "ticker": ticker
    })

    # Create default factory for RoundTableOutput
    def create_default_output():
        return RoundTableOutput(
            signal="neutral",
            confidence=0.0,
            reasoning="Error in generating discussion, defaulting to neutral",
            discussion_summary="Unable to facilitate discussion due to technical error",
            consensus_view="No consensus reached due to error",
            dissenting_opinions="Unable to evaluate dissenting opinions",
            conversation_transcript="Discussion generation failed"
        )

    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=RoundTableOutput,
        agent_name="round_table",
        default_factory=create_default_output,
    ) 