"""
主程序模块 - 对冲基金AI分析系统的核心逻辑
Main module - Core logic for the AI hedge fund analysis system
"""
import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from colorama import Fore, Back, Style, init
import questionary
from agents.ben_graham import ben_graham_agent
from agents.bill_ackman import bill_ackman_agent
from agents.fundamentals import fundamentals_agent
from agents.portfolio_manager import portfolio_management_agent
from agents.technicals import technical_analyst_agent
from agents.risk_manager import risk_management_agent
from agents.sentiment import sentiment_agent
from agents.warren_buffett import warren_buffett_agent
from graph.state import AgentState
from agents.valuation import valuation_agent
from utils.display import print_trading_output
from utils.analysts import ANALYST_ORDER, get_analyst_nodes
from utils.progress import progress
# 移除了 LLM_ORDER 和 get_model_info 的导入，因为模型固定为 GPT-4o
# Removed import of LLM_ORDER and get_model_info as the model is fixed to GPT-4o
# from llm.models import LLM_ORDER, get_model_info
from agents.round_table import round_table

import argparse
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tabulate import tabulate
from utils.visualize import save_graph_as_png
import json

# 从.env文件加载环境变量
# Load environment variables from .env file
load_dotenv()

init(autoreset=True)


def parse_hedge_fund_response(response):
    """
    解析对冲基金响应 - 将响应转换为JSON格式
    Parse hedge fund response - Convert response to JSON format
    """
    import json

    try:
        return json.loads(response)
    except:
        print(f"Error parsing response: {response}")
        return None


##### 运行对冲基金系统 #####
##### Run the Hedge Fund #####
def run_hedge_fund(
    tickers: list[str],
    start_date: str,
    end_date: str,
    portfolio: dict,
    show_reasoning: bool = False,
    selected_analysts: list[str] = [],
):
    """
    运行对冲基金分析系统的主函数
    Main function to run the hedge fund analysis system
    
    Args:
        tickers: 股票代码列表 - List of stock tickers
        start_date: 开始日期 - Start date  
        end_date: 结束日期 - End date
        portfolio: 投资组合信息 - Portfolio information
        show_reasoning: 是否显示推理过程 - Whether to show reasoning
        selected_analysts: 选择的分析师列表 - List of selected analysts
    """
    # Start progress tracking
    progress.start()

    try:
        # 使用指定的分析师创建新的工作流
        # Create a new workflow with the specified analysts
        workflow = create_workflow(selected_analysts)
        
        # Print the selected analysts for debugging
        print(f"\n{Fore.CYAN}Selected analysts for workflow: {selected_analysts}{Style.RESET_ALL}\n")
        
        app = workflow.compile()

        # 创建初始状态 - Create the initial state
        initial_state = {
            "messages": [],
            "data": {
                "tickers": tickers,
                "start_date": start_date,
                "end_date": end_date,
                "portfolio": portfolio,
                "analyst_signals": {},
            },
            "metadata": {
                "show_reasoning": show_reasoning,
                "model_name": "gpt-4o", # 可以硬编码用于元数据目的
                "model_provider": "OpenAI", # 可以硬编码用于元数据目的
            },
        }

        # 运行工作流 - Run the workflow
        result = app.invoke(initial_state)
        
        # Stop progress tracking
        progress.stop()

        # 提取投资组合决策 - Extract the portfolio decisions
        if "portfolio_decision" in result["data"]:
            portfolio_decision = result["data"]["portfolio_decision"]
        else:
            # Handle the case where portfolio_decision might be missing
            # Look for it in portfolio_management_agent output in messages
            for message in reversed(result["messages"]):
                if hasattr(message, "name") and message.name == "portfolio_management_agent":
                    try:
                        portfolio_decision = json.loads(message.content)
                        break
                    except:
                        pass
            else:
                portfolio_decision = {}
                print(f"{Fore.RED}Warning: Could not find portfolio decisions in output{Style.RESET_ALL}")
        
        # Return result with analyst signals for further processing
        return {
            "decisions": portfolio_decision,
            "analyst_signals": result["data"]["analyst_signals"],
        }
    except Exception as e:
        progress.stop()
        print(f"Error running hedge fund: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def start(state: AgentState):
    """
    初始化工作流的输入消息
    Initialize the workflow with the input message.
    """
    return state


def create_workflow(selected_analysts=None):
    """
    创建带有选定分析师的工作流
    Create the workflow with selected analysts.
    """
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # 从配置中获取分析师节点 - Get analyst nodes from the configuration
    analyst_nodes = get_analyst_nodes()
    
    print(f"\n{Fore.YELLOW}Creating workflow with analysts: {selected_analysts}{Style.RESET_ALL}")
    
    # 如果没有选择分析师，默认使用所有分析师
    # Default to all analysts if none selected
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())
        print(f"{Fore.RED}No analysts specified, defaulting to all: {selected_analysts}{Style.RESET_ALL}")
    
    # 添加所有选定的分析师节点 - Add all selected analyst nodes
    for analyst_key in selected_analysts:
        if analyst_key in analyst_nodes:
            node_name, node_func = analyst_nodes[analyst_key]
            workflow.add_node(node_name, node_func)
            workflow.add_edge("start_node", node_name)
        else:
            print(f"{Fore.RED}Warning: Analyst {analyst_key} not found in configuration{Style.RESET_ALL}")
    
    # 始终添加风险管理和投资组合管理 - Always add risk and portfolio management
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("portfolio_management_agent", portfolio_management_agent)
    
    # 将所有分析师连接到风险管理 - Connect all analysts to risk management
    for analyst_key in selected_analysts:
        if analyst_key in analyst_nodes:
            node_name = analyst_nodes[analyst_key][0]
            workflow.add_edge(node_name, "risk_management_agent")
    
    # 将风险管理连接到投资组合管理 - Connect risk management to portfolio management
    workflow.add_edge("risk_management_agent", "portfolio_management_agent")
    workflow.add_edge("portfolio_management_agent", END)

    workflow.set_entry_point("start_node")
    return workflow


# 移除了 is_crypto, model_name, model_provider 参数 (Removed is_crypto, model_name, model_provider parameters)
def run_all_analysts_with_round_table(tickers, start_date, end_date, portfolio, show_reasoning):
    """
    运行所有可用分析师并进行圆桌讨论
    Run all available analysts and then conduct a round table discussion without user selection.
    This is a simplified workflow for when the user specifies the --round-table flag.
    """
    # 获取所有可用的分析师键（除了我们要移除的master）
    # Get all available analyst keys (except master which we're removing)
    analyst_nodes = get_analyst_nodes()
    all_analysts = [key for key in analyst_nodes.keys() if key != "master"]
    
    print(f"\n{Fore.YELLOW}Running all analysts for Round Table discussion:{Style.RESET_ALL}")
    for analyst in all_analysts:
        print(f"  {analyst_nodes[analyst][0].replace('_agent', '').replace('_', ' ').title()}")
    print("")  # Empty line for spacing
    
    # 运行包含所有分析师的常规对冲基金分析
    # Run the regular hedge fund with all analysts
    # 调用 run_hedge_fund 时不再传递 model_name 和 model_provider
    # model_name and model_provider are no longer passed when calling run_hedge_fund
    result = run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=show_reasoning,
        selected_analysts=all_analysts,
    )
    
    # 运行圆桌讨论 - Run the round table discussion
    # 调用 run_round_table 时不再传递 model_name 和 model_provider
    # model_name and model_provider are no longer passed when calling run_round_table
    from round_table import run_round_table # 确保此导入在文件顶部 (Ensure this import is at the top of the file)
    round_table_results = run_round_table(
        data={
            "tickers": tickers,
            "analyst_signals": result["analyst_signals"]
        },
        show_reasoning=show_reasoning
    )
    
    # Add the round table results to the analyst signals
    result["analyst_signals"]["round_table"] = round_table_results
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the hedge fund trading system")
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=100000.0,
        help="Initial cash position. Defaults to 100000.0)"
    )
    parser.add_argument(
        "--margin-requirement",
        type=float,
        default=0.0,
        help="Initial margin requirement. Defaults to 0.0"
    )
    parser.add_argument("--tickers", type=str, required=True, help="Comma-separated list of stock ticker symbols")
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD). Defaults to 3 months before end date",
    )
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to today")
    parser.add_argument("--show-reasoning", action="store_true", help="Show reasoning from each agent")
    parser.add_argument(
        "--show-agent-graph", action="store_true", help="Show the agent graph"
    )
    parser.add_argument(
        "--round-table",
        action="store_true",
        help="Run an investment round table discussion after individual analyst evaluations"
    )
    parser.add_argument(
        "--crypto",
        action="store_true",
        help="Analyze cryptocurrency instead of stocks (append -USD to ticker symbols)"
    )
    # 移除了 --crypto 参数的解析和相关逻辑，因为不再支持加密货币
    # Removed --crypto argument parsing and related logic as cryptocurrency is no longer supported.
    # parser.add_argument(
    #     "--crypto",
    #     action="store_true",
    #     help="Analyze cryptocurrency instead of stocks (append -USD to ticker symbols)"
    # )

    args = parser.parse_args()

    # Parse tickers from comma-separated string
    tickers = [ticker.strip() for ticker in args.tickers.split(",")]
   
    print(f"\n{Fore.CYAN}Using fixed LLM model: {Fore.GREEN + Style.BRIGHT}OpenAI GPT-4o{Style.RESET_ALL}\n")


    # Validate dates if provided
    if args.start_date:
        try:
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Start date must be in YYYY-MM-DD format")

    if args.end_date:
        try:
            datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("End date must be in YYYY-MM-DD format")

    # Set the start and end dates
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    if not args.start_date:
        # Calculate 3 months before end_date
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")
    else:
        start_date = args.start_date

    # Initialize portfolio with cash amount and stock positions
    portfolio = {
        "cash": args.initial_cash,  # Initial cash amount
        "margin_requirement": args.margin_requirement,  # Initial margin requirement
        "positions": {
            ticker: {
                "long": 0,  # Number of shares held long
                "short": 0,  # Number of shares held short
                "long_cost_basis": 0.0,  # Average cost basis for long positions
                "short_cost_basis": 0.0,  # Average price at which shares were sold short
            } for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,  # Realized gains from long positions
                "short": 0.0,  # Realized gains from short positions
            } for ticker in tickers
        }
    }

    # Bypass analyst selection when round table is specified
    if args.round_table:
        # Run all analysts and round table without requiring user selection
        result = run_all_analysts_with_round_table(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            portfolio=portfolio,
            show_reasoning=args.show_reasoning,
        )
        print_trading_output(result)
    else:
        # Regular flow - prompt user to select analysts
        selected_analysts = None
        choices = questionary.checkbox(
            "Select your AI analysts.",
            choices=[questionary.Choice(display, value=value) for display, value in ANALYST_ORDER],
            instruction="\n\nInstructions: \n1. Press Space to select/unselect analysts.\n2. Press 'a' to select/unselect all.\n3. Press Enter when done to run the hedge fund.\n",
            validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
            style=questionary.Style(
                [
                    ("checkbox-selected", "fg:green"),
                    ("selected", "fg:green noinherit"),
                    ("highlighted", "noinherit"),
                    ("pointer", "noinherit"),
                ]
            ),
        ).ask()
        
        if not choices:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)
        else:
            selected_analysts = choices
            print(f"\nSelected analysts: {', '.join(Fore.GREEN + choice.title().replace('_', ' ') + Style.RESET_ALL for choice in choices)}\n")

        # Create workflow for visualization if requested
        if args.show_agent_graph:
            workflow = create_workflow(selected_analysts)
            app = workflow.compile()
            
            file_path = ""
            for selected_analyst in selected_analysts:
                file_path += selected_analyst + "_"
            file_path += "graph.png"
            save_graph_as_png(app, file_path)

        # Run the hedge fund with is_crypto flag
        result = run_hedge_fund(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            portfolio=portfolio,
            show_reasoning=args.show_reasoning,
            selected_analysts=selected_analysts,
        )
        print_trading_output(result)
