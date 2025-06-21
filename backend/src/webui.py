#!/usr/bin/env python3
"""
Web UI 主程序 - 提供网页界面用于运行AI对冲基金分析系统
Main Web UI program - Provides web interface for running AI hedge fund analysis system
"""
import os
import sys
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 从.env文件加载环境变量
# Load environment variables from .env file
load_dotenv()

# 配置常量
# Configuration
API_PORT = 5000
DEFAULT_HOST = "0.0.0.0"

# API服务器实现
def start_api_server(host=DEFAULT_HOST, port=API_PORT):
    """启动API服务器 - 提供后端API接口"""
    try:
        from main import run_hedge_fund
        from backtester import Backtester
        from utils.analysts import ANALYST_ORDER
    except ImportError as e:
        print(f"Error importing modules: {e}")
        traceback.print_exc()
        return

    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # @app.route('/api/models', methods=['GET'])
    # def get_models():
    #     """获取可用的LLM模型列表"""
    #     hardcoded_llm_order = [("[openai] gpt-4o", "gpt-4o", "OpenAI")]
    #     return jsonify({"models": hardcoded_llm_order})

    @app.route('/api/hello', methods=['GET'])
    def hello():
        return jsonify({"message": "Hello, World!"})
    
    @app.route('/api/getAppleFinancialMetrics', methods=['GET'])
    def get_apple_financial_metrics():
        from tools.api import get_financial_metrics
        metrics = get_financial_metrics("AAPL", "2024-03-31")
        # Convert Pydantic models to dictionaries for JSON serialization
        return jsonify([m.model_dump() for m in metrics])

    @app.route('/api/analysts', methods=['GET'])
    def get_analysts():
        """获取可用的分析师代理列表"""
        return jsonify({"analysts": ANALYST_ORDER})

    @app.route('/api/analysis', methods=['POST'])
    def run_analysis():
        """运行股票分析"""
        try:
            data = request.get_json()
            ticker_list = data.get('tickers', '').split(',')
            selected_analysts = data.get('selectedAnalysts', [])
            
            print(f"Processing analysis for tickers: {ticker_list}")
            print(f"Selected analysts: {selected_analysts}")
            
            result = run_hedge_fund_for_web(
                tickers=ticker_list,
                selected_analysts=selected_analysts,
                start_date=data.get('startDate'),
                end_date=data.get('endDate'),
            )
            
            print("Analysis completed successfully")
            return jsonify(result)
        
        except Exception as e:
            print(f"API error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({"error": str(e)}), 500

    # @app.route('/api/backtest', methods=['POST'])
    # def run_backtest():
        """运行历史数据回测"""
        try:
            data = request.get_json()
            tickers = data.get('tickers', '').split(',')
            start_date = data.get('startDate')
            end_date = data.get('endDate')
            selected_analysts = data.get('selectedAnalysts', [])
            initial_capital = data.get('initialCapital', 100000)
            margin_requirement = data.get('marginRequirement', 0.5)
            
            # 处理可选日期
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            if not start_date:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                start_date_obj = end_date_obj - timedelta(days=90)
                start_date = start_date_obj.strftime('%Y-%m-%d')
            
            backtester = Backtester(
                agent=run_hedge_fund,
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                selected_analysts=selected_analysts,
                initial_margin_requirement=margin_requirement,
            )
            
            performance_metrics = backtester.run_backtest()
            performance_df = backtester.analyze_performance()
            performance_data = performance_df.to_dict(orient='records')
            
            return jsonify({
                "metrics": performance_metrics,
                "performance": performance_data
            })
            
        except Exception as e:
            return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

    # @app.route('/api/round-table', methods=['POST'])
    # def run_round_table():
    #     """运行圆桌讨论"""
    #     try:
    #         from round_table.main import run_round_table
            
    #         data = request.get_json()
    #         ticker = data.get('ticker')
            
    #         analysis_data = {
    #             "tickers": [ticker],
    #             "analyst_signals": {}
    #         }
            
    #         result = run_round_table(
    #             data=analysis_data, 
    #             show_reasoning=True
    #         )
            
    #         return jsonify(result)
            
    #     except Exception as e:
    #         return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

    # @app.route('/api/env', methods=['GET'])
    # def get_env_vars():
    #     """返回相关环境变量（不暴露敏感API密钥）"""
    #     return jsonify({
    #         "openai_api_configured": bool(os.getenv("OPENAI_API_KEY")),
    #         "anthropic_api_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
    #         "groq_api_configured": bool(os.getenv("GROQ_API_KEY")),
    #         "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
    #     })

    # print(f"Starting API server at http://{host}:{port}")
    app.run(host=host, port=port, debug=True, use_reloader=False)

def run_hedge_fund_for_web(tickers, selected_analysts, start_date=None, end_date=None, initial_cash=100000):
    """为Web UI优化的股票分析函数"""
    from graph.state import AgentState
    
    print("Starting analysis process")
    
    # 创建投资组合
    portfolio = {
        "cash": initial_cash,
        "positions": {},
        "cost_basis": {}, 
        "realized_gains": {ticker: {"long": 0.0, "short": 0.0} for ticker in tickers}
    }
    
    # 创建初始状态
    initial_state = {
        "messages": [],
        "data": {
            "tickers": tickers,
            "portfolio": portfolio,
            "start_date": start_date if start_date else (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": end_date if end_date else datetime.now().strftime("%Y-%m-%d"),
            "analyst_signals": {},
        },
        "metadata": {
            "show_reasoning": True,
            "model_name": "gpt-4o",
            "model_provider": "OpenAI"
        }
    }
    
    print(f"Analyzing tickers: {tickers}")
    print(f"Using analysts: {selected_analysts}")
    
    # 导入分析师代理
    from agents.warren_buffett import warren_buffett_agent
    from agents.bill_ackman import bill_ackman_agent
    from agents.ben_graham import ben_graham_agent
    from agents.charlie_munger import charlie_munger_agent
    from agents.cathie_wood import cathie_wood_agent
    from agents.peter_lynch import peter_lynch_agent
    from agents.portfolio_manager import portfolio_management_agent
    
    agent_map = {
        "warren_buffett_agent": warren_buffett_agent,
        "bill_ackman_agent": bill_ackman_agent,
        "ben_graham_agent": ben_graham_agent,
        "charlie_munger_agent": charlie_munger_agent,
        "cathie_wood_agent": cathie_wood_agent,
        "peter_lynch_agent": peter_lynch_agent,
        "portfolio_management_agent": portfolio_management_agent
    }
    
    state = initial_state
    
    # 运行每个选定的分析师
    for analyst_name in selected_analysts:
        if analyst_name in agent_map:
            print(f"Running analyst: {analyst_name}")
            try:
                agent_fn = agent_map[analyst_name]
                result = agent_fn(AgentState(state))
                
                if result:
                    if "messages" in result:
                        state["messages"] = result["messages"]
                    if "data" in result:
                        state["data"] = result["data"]
                
                print(f"Completed {analyst_name} analysis")
            except Exception as e:
                print(f"Error in {analyst_name}: {str(e)}")
                print(traceback.format_exc())
    
    # 准备最终输出
    result = {"ticker_analyses": {}}
    analyst_signals = state["data"].get("analyst_signals", {})

    for ticker in tickers:
        result["ticker_analyses"][ticker] = []
        
        for analyst_name in selected_analysts:
            analyst_result = {
                "agent_name": analyst_name,
                "signal": "中性",
                "confidence": 50.0,
                "reasoning": "分析正在进行中..."
            }
            
            if analyst_name in analyst_signals and ticker in analyst_signals[analyst_name]:
                analyst_data = analyst_signals[analyst_name][ticker]
                
                if "signal" in analyst_data:
                    analyst_result["signal"] = analyst_data["signal"]
                
                if "confidence" in analyst_data:
                    analyst_result["confidence"] = analyst_data["confidence"]
                
                if "reasoning" in analyst_data:
                    analyst_result["reasoning"] = analyst_data["reasoning"]
            
            result["ticker_analyses"][ticker].append(analyst_result)
    
    print("Analysis completed successfully")
    return result

if __name__ == "__main__":
    print("Starting Hedge Fund AI API Server...")
    print(f"API server will be available at http://{DEFAULT_HOST}:{API_PORT}")
    
    try:
        start_api_server()
    except KeyboardInterrupt:
        print("\nShutting down API server...") 