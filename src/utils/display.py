from colorama import Fore, Style
from tabulate import tabulate
from .analysts import ANALYST_ORDER
import os


def sort_analyst_signals(signals):
    """Sort analyst signals in a consistent order."""
    # Create order mapping from ANALYST_ORDER
    analyst_order = {display: idx for idx, (display, _) in enumerate(ANALYST_ORDER)}
    analyst_order["Risk Management"] = len(ANALYST_ORDER)  # Add Risk Management at the end

    return sorted(signals, key=lambda x: analyst_order.get(x[0], 999))


def print_trading_output(result: dict) -> None:
    """
    Print formatted trading results with colored tables for multiple tickers.

    Args:
        result (dict): Dictionary containing decisions and analyst signals for multiple tickers
    """
    decisions = result.get("decisions")
    if not decisions:
        print(f"{Fore.RED}No trading decisions available{Style.RESET_ALL}")
        return

    # Print decisions for each ticker
    for ticker, decision in decisions.items():
        print(f"\n{Fore.WHITE}{Style.BRIGHT}Analysis for {Fore.CYAN}{ticker}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{Style.BRIGHT}{'=' * 50}{Style.RESET_ALL}")

        # Prepare analyst signals table for this ticker
        table_data = []
        for agent, signals in result.get("analyst_signals", {}).items():
            if ticker not in signals:
                continue

            signal = signals[ticker]
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            signal_type = signal.get("signal", "").upper()

            signal_color = {
                "BULLISH": Fore.GREEN,
                "BEARISH": Fore.RED,
                "NEUTRAL": Fore.YELLOW,
            }.get(signal_type, Fore.WHITE)

            table_data.append(
                [
                    f"{Fore.CYAN}{agent_name}{Style.RESET_ALL}",
                    f"{signal_color}{signal_type}{Style.RESET_ALL}",
                    f"{Fore.YELLOW}{signal.get('confidence')}%{Style.RESET_ALL}",
                ]
            )

        # Sort the signals according to the predefined order
        table_data = sort_analyst_signals(table_data)

        print(f"\n{Fore.WHITE}{Style.BRIGHT}ANALYST SIGNALS:{Style.RESET_ALL} [{Fore.CYAN}{ticker}{Style.RESET_ALL}]")
        print(
            tabulate(
                table_data,
                headers=[f"{Fore.WHITE}Analyst", "Signal", "Confidence"],
                tablefmt="grid",
                colalign=("left", "center", "right"),
            )
        )

        # Print Trading Decision Table
        action = decision.get("action", "").upper()
        action_color = {"BUY": Fore.GREEN, "SELL": Fore.RED, "HOLD": Fore.YELLOW}.get(action, Fore.WHITE)

        decision_data = [
            ["Action", f"{action_color}{action}{Style.RESET_ALL}"],
            ["Quantity", f"{action_color}{decision.get('quantity')}{Style.RESET_ALL}"],
            [
                "Confidence",
                f"{Fore.YELLOW}{decision.get('confidence'):.1f}%{Style.RESET_ALL}",
            ],
        ]

        print(f"\n{Fore.WHITE}{Style.BRIGHT}TRADING DECISION:{Style.RESET_ALL} [{Fore.CYAN}{ticker}{Style.RESET_ALL}]")
        print(tabulate(decision_data, tablefmt="grid", colalign=("left", "right")))

        # Print Reasoning
        print(f"\n{Fore.WHITE}{Style.BRIGHT}Reasoning:{Style.RESET_ALL} {Fore.CYAN}{decision.get('reasoning')}{Style.RESET_ALL}")

    # Print Portfolio Summary
    print(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY:{Style.RESET_ALL}")
    portfolio_data = []
    for ticker, decision in decisions.items():
        action = decision.get("action", "").upper()
        action_color = {
            "BUY": Fore.GREEN,
            "SELL": Fore.RED,
            "HOLD": Fore.YELLOW,
            "COVER": Fore.GREEN,
            "SHORT": Fore.RED,
        }.get(action, Fore.WHITE)
        portfolio_data.append(
            [
                f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",
                f"{action_color}{action}{Style.RESET_ALL}",
                f"{action_color}{decision.get('quantity')}{Style.RESET_ALL}",
                f"{Fore.YELLOW}{decision.get('confidence'):.1f}%{Style.RESET_ALL}",
            ]
        )

    print(
        tabulate(
            portfolio_data,
            headers=[f"{Fore.WHITE}Ticker", "Action", "Quantity", "Confidence"],
            tablefmt="grid",
            colalign=("left", "center", "right", "right"),
        )
    )


def print_backtest_results(table_rows: list) -> None:
    """Print the backtest results in a nicely formatted table"""
    # Clear the screen
    os.system("cls" if os.name == "nt" else "clear")

    # Split rows into ticker rows and summary rows
    ticker_rows = []
    summary_rows = []

    for row in table_rows:
        if isinstance(row[1], str) and "PORTFOLIO SUMMARY" in row[1]:
            summary_rows.append(row)
        else:
            ticker_rows.append(row)

    
    # Display latest portfolio summary
    if summary_rows:
        latest_summary = summary_rows[-1]
        print(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY:{Style.RESET_ALL}")

        # Extract values and remove commas before converting to float
        cash_str = latest_summary[7].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        position_str = latest_summary[6].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")
        total_str = latest_summary[8].split("$")[1].split(Style.RESET_ALL)[0].replace(",", "")

        print(f"Cash Balance: {Fore.CYAN}${float(cash_str):,.2f}{Style.RESET_ALL}")
        print(f"Total Position Value: {Fore.YELLOW}${float(position_str):,.2f}{Style.RESET_ALL}")
        print(f"Total Value: {Fore.WHITE}${float(total_str):,.2f}{Style.RESET_ALL}")
        print(f"Return: {latest_summary[9]}")
        
        # Display performance metrics if available
        if latest_summary[10]:  # Sharpe ratio
            print(f"Sharpe Ratio: {latest_summary[10]}")
        if latest_summary[11]:  # Sortino ratio
            print(f"Sortino Ratio: {latest_summary[11]}")
        if latest_summary[12]:  # Max drawdown
            print(f"Max Drawdown: {latest_summary[12]}")

    # Add vertical spacing
    print("\n" * 2)

    # Print the table with just ticker rows
    print(
        tabulate(
            ticker_rows,
            headers=[
                "Date",
                "Ticker",
                "Action",
                "Quantity",
                "Price",
                "Shares",
                "Position Value",
                "Bullish",
                "Bearish",
                "Neutral",
            ],
            tablefmt="grid",
            colalign=(
                "left",  # Date
                "left",  # Ticker
                "center",  # Action
                "right",  # Quantity
                "right",  # Price
                "right",  # Shares
                "right",  # Position Value
                "right",  # Bullish
                "right",  # Bearish
                "right",  # Neutral
            ),
        )
    )

    # Add vertical spacing
    print("\n" * 4)


def format_backtest_row(
    date: str,
    ticker: str,
    action: str,
    quantity: float,
    price: float,
    shares_owned: float,
    position_value: float,
    bullish_count: int,
    bearish_count: int,
    neutral_count: int,
    is_summary: bool = False,
    total_value: float = None,
    return_pct: float = None,
    cash_balance: float = None,
    total_position_value: float = None,
    sharpe_ratio: float = None,
    sortino_ratio: float = None,
    max_drawdown: float = None,
) -> list[any]:
    """Format a row for the backtest results table"""
    # Color the action
    action_color = {
        "BUY": Fore.GREEN,
        "COVER": Fore.GREEN,
        "SELL": Fore.RED,
        "SHORT": Fore.RED,
        "HOLD": Fore.YELLOW,
    }.get(action.upper(), Fore.WHITE)

    if is_summary:
        return_color = Fore.GREEN if return_pct >= 0 else Fore.RED
        return [
            date,
            f"{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY{Style.RESET_ALL}",
            "",  # Action
            "",  # Quantity
            "",  # Price
            "",  # Shares
            f"{Fore.YELLOW}${total_position_value:,.2f}{Style.RESET_ALL}",  # Total Position Value
            f"{Fore.CYAN}${cash_balance:,.2f}{Style.RESET_ALL}",  # Cash Balance
            f"{Fore.WHITE}${total_value:,.2f}{Style.RESET_ALL}",  # Total Value
            f"{return_color}{return_pct:+.2f}%{Style.RESET_ALL}",  # Return
            f"{Fore.YELLOW}{sharpe_ratio:.2f}{Style.RESET_ALL}" if sharpe_ratio is not None else "",  # Sharpe Ratio
            f"{Fore.YELLOW}{sortino_ratio:.2f}{Style.RESET_ALL}" if sortino_ratio is not None else "",  # Sortino Ratio
            f"{Fore.RED}{max_drawdown:.2f}%{Style.RESET_ALL}" if max_drawdown is not None else "",  # Max Drawdown
        ]
    else:
        return [
            date,
            f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",
            f"{action_color}{action.upper()}{Style.RESET_ALL}",
            f"{action_color}{quantity:,.0f}{Style.RESET_ALL}",
            f"{Fore.WHITE}{price:,.2f}{Style.RESET_ALL}",
            f"{Fore.WHITE}{shares_owned:,.0f}{Style.RESET_ALL}",
            f"{Fore.YELLOW}{position_value:,.2f}{Style.RESET_ALL}",
            f"{Fore.GREEN}{bullish_count}{Style.RESET_ALL}",
            f"{Fore.RED}{bearish_count}{Style.RESET_ALL}",
            f"{Fore.BLUE}{neutral_count}{Style.RESET_ALL}",
        ]


def print_analyst_signals_only(result: dict) -> None:
    """
    只打印投资专家agent的分析信号，不包含投资组合决策
    Print only analyst signals from investment expert agents without portfolio decisions.

    Args:
        result (dict): Dictionary containing analyst signals for multiple tickers
    """
    analyst_signals = result.get("analyst_signals", {})
    if not analyst_signals:
        print(f"{Fore.RED}No analyst signals available{Style.RESET_ALL}")
        return

    # 获取所有股票代码 - Get all tickers
    all_tickers = set()
    for agent_signals in analyst_signals.values():
        all_tickers.update(agent_signals.keys())
    
    if not all_tickers:
        print(f"{Fore.RED}No ticker analysis found{Style.RESET_ALL}")
        return

    # Signal normalization function
    def normalize_signal(signal_str):
        """Normalize signals to English for consistent processing"""
        if not signal_str:
            return ""
        signal_lower = signal_str.lower().strip()
        # Handle Chinese signals
        if signal_lower in ["看涨", "买入", "bullish", "buy"]:
            return "bullish"
        elif signal_lower in ["看跌", "卖出", "bearish", "sell"]:
            return "bearish"
        elif signal_lower in ["中性", "持有", "neutral", "hold"]:
            return "neutral"
        else:
            return "neutral"  # default to neutral for unknown signals

    # 为每个股票代码打印分析师信号 - Print analyst signals for each ticker
    for ticker in sorted(all_tickers):
        print(f"\n{Fore.WHITE}{Style.BRIGHT}Analysis for {Fore.CYAN}{ticker}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{Style.BRIGHT}{'=' * 50}{Style.RESET_ALL}")

        # 准备分析师信号表格数据 - Prepare analyst signals table data for this ticker
        table_data = []
        for agent, signals in analyst_signals.items():
            if ticker not in signals:
                continue

            signal = signals[ticker]
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            signal_type = signal.get("signal", "").upper()

            # Normalize signal for color coding
            normalized_signal = normalize_signal(signal.get("signal", ""))
            signal_color = {
                "bullish": Fore.GREEN,
                "bearish": Fore.RED,
                "neutral": Fore.YELLOW,
            }.get(normalized_signal, Fore.WHITE)

            table_data.append(
                [
                    f"{Fore.CYAN}{agent_name}{Style.RESET_ALL}",
                    f"{signal_color}{signal_type}{Style.RESET_ALL}",
                    f"{Fore.YELLOW}{signal.get('confidence', 'N/A')}%{Style.RESET_ALL}",
                    f"{Fore.WHITE}{signal.get('reasoning', 'No reasoning provided')[:100]}...{Style.RESET_ALL}" if len(signal.get('reasoning', '')) > 100 else f"{Fore.WHITE}{signal.get('reasoning', 'No reasoning provided')}{Style.RESET_ALL}"
                ]
            )

        # 按照预定义顺序排列信号 - Sort the signals according to the predefined order
        table_data = sort_analyst_signals(table_data)

        print(f"\n{Fore.WHITE}{Style.BRIGHT}ANALYST SIGNALS:{Style.RESET_ALL} [{Fore.CYAN}{ticker}{Style.RESET_ALL}]")
        if table_data:
            print(
                tabulate(
                    table_data,
                    headers=[f"{Fore.WHITE}Analyst", "Signal", "Confidence", "Reasoning"],
                    tablefmt="grid",
                    colalign=("left", "center", "right", "left"),
                )
            )
        else:
            print(f"{Fore.YELLOW}No analyst signals found for {ticker}{Style.RESET_ALL}")

        # 打印详细推理（如果有的话） - Print detailed reasoning if available
        print(f"\n{Fore.WHITE}{Style.BRIGHT}DETAILED ANALYSIS:{Style.RESET_ALL}")
        for agent, signals in analyst_signals.items():
            if ticker not in signals:
                continue
            
            signal = signals[ticker]
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            reasoning = signal.get('reasoning', 'No detailed reasoning provided')
            
            print(f"\n{Fore.CYAN}{Style.BRIGHT}{agent_name}:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{reasoning}{Style.RESET_ALL}")

    # 打印分析师总结 - Print analyst summary
    print(f"\n{Fore.WHITE}{Style.BRIGHT}ANALYST SUMMARY:{Style.RESET_ALL}")
    summary_data = []
    for ticker in sorted(all_tickers):
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        
        for agent, signals in analyst_signals.items():
            if ticker in signals:
                signal_type = normalize_signal(signals[ticker].get("signal", ""))
                if signal_type == "bullish":
                    bullish_count += 1
                elif signal_type == "bearish":
                    bearish_count += 1
                elif signal_type == "neutral":
                    neutral_count += 1
        
        # 确定总体情绪 - Determine overall sentiment
        total_signals = bullish_count + bearish_count + neutral_count
        if total_signals > 0:
            if bullish_count > bearish_count and bullish_count > neutral_count:
                overall = f"{Fore.GREEN}BULLISH{Style.RESET_ALL}"
            elif bearish_count > bullish_count and bearish_count > neutral_count:
                overall = f"{Fore.RED}BEARISH{Style.RESET_ALL}"
            else:
                overall = f"{Fore.YELLOW}MIXED{Style.RESET_ALL}"
        else:
            overall = f"{Fore.WHITE}NO SIGNALS{Style.RESET_ALL}"
        
        summary_data.append(
            [
                f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",
                f"{Fore.GREEN}{bullish_count}{Style.RESET_ALL}",
                f"{Fore.RED}{bearish_count}{Style.RESET_ALL}",
                f"{Fore.YELLOW}{neutral_count}{Style.RESET_ALL}",
                overall
            ]
        )

    print(
        tabulate(
            summary_data,
            headers=[f"{Fore.WHITE}Ticker", "Bullish", "Bearish", "Neutral", "Overall"],
            tablefmt="grid",
            colalign=("left", "center", "center", "center", "center"),
        )
    )
