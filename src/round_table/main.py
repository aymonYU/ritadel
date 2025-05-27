from graph.state import show_agent_reasoning
from utils.progress import progress
from colorama import Fore, Style
from round_table.engine import simulate_round_table
from round_table.display import print_readable_conversation, get_signal_color

def run_round_table(data, model_name, model_provider, show_reasoning=True):
    """
    Simulates a round table discussion among investment analysts based on their signals.
    
    This is a standalone feature that synthesizes the analysis of various agents
    into a comprehensive investment decision through simulated dialogue.
    
    Args:
        data: Dictionary containing analyst signals and ticker information
        model_name: Name of the LLM model to use
        model_provider: Provider of the LLM model
        show_reasoning: Whether to print the detailed conversation
        
    Returns:
        Dictionary containing the round table decision for each ticker
    """
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Investment Round Table Discussion{Style.RESET_ALL}")
    
    analyst_signals = data.get("analyst_signals", {})
    tickers = data.get("tickers", [])
    
    if not analyst_signals:
        print(f"{Fore.RED}No analyst signals available for round table discussion{Style.RESET_ALL}")
        return {}
    
    print(f"Available signals from: {list(analyst_signals.keys())}")
    
    # Skip risk management and portfolio management signals
    filtered_signals = {
        agent: signals for agent, signals in analyst_signals.items() 
        if agent not in ["risk_management_agent", "round_table"]
    }
    
    # Initialize round table analysis for each ticker
    round_table_analysis = {}
    
    for ticker in tickers:
        progress.update_status("round_table", ticker, "Collecting analyst inputs")
        
        # Collect all individual agent signals for this ticker
        ticker_signals = {}
        for agent_name, signals in filtered_signals.items():
            if ticker in signals:
                ticker_signals[agent_name] = signals[ticker]
        
        if not ticker_signals:
            progress.update_status("round_table", ticker, "No signals found for discussion")
            print(f"{Fore.RED}No analyst signals found for {ticker}. Cannot conduct round table.{Style.RESET_ALL}")
            continue
        
        print(f"{Fore.CYAN}Found {len(ticker_signals)} analyst signals for {ticker}{Style.RESET_ALL}")
        progress.update_status("round_table", ticker, f"Simulating discussion with {len(ticker_signals)} analysts")
        
        # Simulate the round table discussion
        # 调用 simulate_round_table 时不再传递 model_name 和 model_provider
        # model_name and model_provider are no longer passed when calling simulate_round_table
        round_table_output = simulate_round_table(
            ticker=ticker,
            ticker_signals=ticker_signals,
            # model_name=model_name, # 已移除 (Removed)
            # model_provider=model_provider, # 已移除 (Removed)
        )
        
        # Store analysis
        round_table_analysis[ticker] = {
            "signal": round_table_output.signal,
            "confidence": round_table_output.confidence,
            "reasoning": round_table_output.reasoning,
            "discussion_summary": round_table_output.discussion_summary,
            "consensus_view": round_table_output.consensus_view,
            "dissenting_opinions": round_table_output.dissenting_opinions,
            "conversation_transcript": round_table_output.conversation_transcript
        }
        
        # Always print the header to show we're running
        print(f"\n{Fore.WHITE}{Style.BRIGHT}===== INVESTMENT ROUND TABLE: {Fore.CYAN}{ticker}{Fore.WHITE} ====={Style.RESET_ALL}")
        
        # Print the conversation transcript in a readable format
        if show_reasoning:
            print_readable_conversation(round_table_output.conversation_transcript)
            print(f"\n{Fore.WHITE}{Style.BRIGHT}===== CONCLUSION ====={Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Signal: {get_signal_color(round_table_output.signal)}{round_table_output.signal.upper()}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Confidence: {Fore.WHITE}{round_table_output.confidence}%{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Reasoning: {Fore.WHITE}{round_table_output.reasoning}{Style.RESET_ALL}\n")
        else:
            # Print just a summary if show_reasoning is off
            transcript_preview = round_table_output.conversation_transcript.split('\n')[:5]
            print('\n'.join(transcript_preview))
            print(f"{Fore.YELLOW}... [Set --show-reasoning to see full conversation] ...{Style.RESET_ALL}")
            
        print(f"{Fore.WHITE}{Style.BRIGHT}{'=' * 80}{Style.RESET_ALL}\n")
        progress.update_status("round_table", ticker, "Discussion completed")
    
    # Display the comprehensive analysis if requested
    if show_reasoning:
        show_agent_reasoning(round_table_analysis, "Investment Round Table")
    
    return round_table_analysis 