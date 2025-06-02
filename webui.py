#!/usr/bin/env python3
"""
Web UI 主程序 - 提供网页界面用于运行AI对冲基金分析系统
Main Web UI program - Provides web interface for running AI hedge fund analysis system
"""
import os
import sys
import subprocess
import webbrowser
import time
import shutil
import json
import threading
from pathlib import Path
import traceback
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask_sock import Sock
import queue
import io
import contextlib
import builtins  # Add this import at the top of the file
from colorama import Fore, Style, init

# 从.env文件加载环境变量
# Load environment variables from .env file
load_dotenv()

# 配置常量
# Configuration
WEBUI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webui")
DEFAULT_PORT = 3000
DEFAULT_HOST = "127.0.0.1"
API_PORT = 5000

# 将src目录添加到Python路径
# Add src directory to Python path
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.append(SRC_DIR)

# Add these imports at the top of the file if they're not already there
import io
import sys
import traceback

# Then move the VerboseLogger class near the top of the file,
# right after your imports and before functions that use it
# (around line 40 after the imports and before start_api_server)

# 全局WebSocket客户端列表
# Add a global function for server-wide logging to websocket clients
websocket_clients = []

def broadcast_log(message, level="info"):
    """
    广播日志消息到所有WebSocket客户端
    Broadcast log message to all WebSocket clients
    """
    # Send to WebSocket clients
    log_data = {"level": level, "message": message}
    for client in websocket_clients[:]:
        try:
            client.send(json.dumps(log_data))
        except Exception:
            websocket_clients.remove(client)

# 创建自定义进度处理器，将消息转发到websocket
# Create a custom progress handler that forwards to websocket
class WebUIProgressHandler:
    """
    Web UI进度处理器 - 处理分析过程中的状态更新
    Web UI progress handler - Handles status updates during analysis process
    """
    def __init__(self):
        pass
        
    def update_status(self, agent, ticker, status):
        """
        更新分析状态并广播给客户端
        Update analysis status and broadcast to clients
        """
        # Format the status message
        if ticker:
            message = f"[{agent}] {ticker}: {status}"
        else:
            message = f"[{agent}] {status}"
        
        # Broadcast to all websocket clients
        broadcast_log(message, "info")
        
    def start(self):
        """开始分析过程 - Start analysis process"""
        broadcast_log("Starting analysis process", "info")
        
    def complete(self):
        """完成分析过程 - Complete analysis process"""
        broadcast_log("Analysis process completed", "success")

# 捕获所有Python输出的详细日志记录器
# Class to capture all Python output including LLM responses
class VerboseLogger:
    """
    详细日志记录器 - 捕获函数执行过程中的所有输出
    Verbose logger - Captures all output during function execution
    """
    def __init__(self, original_func):
        self.original_func = original_func
    
    def __call__(self, *args, **kwargs):
        """
        包装函数调用，捕获并记录所有输出
        Wrap function call to capture and log all output
        """
        # Log the start of the function
        broadcast_log(f"Starting {self.original_func.__name__} with args: {args}", "info")
        
        # Store original stdout and stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # Create string buffers to capture output
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        # Replace with our capturing buffers
        sys.stdout = StdoutTee(original_stdout, stdout_buffer)
        sys.stderr = StdoutTee(original_stderr, stderr_buffer)
        
        try:
            # Run the original function
            result = self.original_func(*args, **kwargs)
            
            # Capture any remaining output
            stdout_content = stdout_buffer.getvalue()
            stderr_content = stderr_buffer.getvalue()
            
            # Log detailed output
            if stdout_content:
                for line in stdout_content.split('\n'):
                    if line.strip():
                        broadcast_log(line, "info")
            
            if stderr_content:
                for line in stderr_content.split('\n'):
                    if line.strip():
                        broadcast_log(line, "error")
            
            # Return the result
            return result
        
        except Exception as e:
            # Log exception
            broadcast_log(f"Error in {self.original_func.__name__}: {str(e)}", "error")
            broadcast_log(traceback.format_exc(), "error")
            raise
        
        finally:
            # Restore stdout and stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr

# 输出分流器类 - 同时输出到原始流和缓冲区
# Class to tee output to both original stream and buffer
class StdoutTee:
    """
    标准输出分流器 - 将输出同时发送到原始流和缓冲区
    Standard output tee - Sends output to both original stream and buffer
    """
    def __init__(self, original_stream, buffer):
        self.original_stream = original_stream
        self.buffer = buffer
    
    def write(self, text):
        """写入文本到两个输出流 - Write text to both output streams"""
        self.original_stream.write(text)
        self.buffer.write(text)
        
        # Forward to WebSocket clients immediately
        if text.strip():
            broadcast_log(text.strip(), "info")
    
    def flush(self):
        """刷新输出流 - Flush output streams"""
        self.original_stream.flush()
        self.buffer.flush()

# 复制.env文件到webui目录以供Next.js访问
# Copy .env file to webui directory for Next.js to access via env vars
def copy_env_file():
    """
    复制环境配置文件到Web UI目录
    Copy environment configuration file to Web UI directory
    """
    src_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    webui_env = os.path.join(WEBUI_DIR, ".env")
    if os.path.exists(src_env):
        shutil.copy2(src_env, webui_env)
        print(f"Copied .env file to {webui_env}")
    else:
        print("Warning: .env file not found in project root")

# API服务器实现
# API server implementation
def start_api_server(host=DEFAULT_HOST, port=API_PORT):
    """
    启动API服务器 - 提供后端API接口
    Start API server - Provides backend API endpoints
    """
    # Try importing the main hedge fund modules
    try:
        from src.main import run_hedge_fund
        from src.backtester import Backtester
        # 移除了 LLM_ORDER 和 get_model_info 的导入，因为模型固定为 GPT-4o
        # Removed import of LLM_ORDER and get_model_info as the model is fixed to GPT-4o
        # from src.llm.models import LLM_ORDER, get_model_info 
        from src.utils.analysts import ANALYST_ORDER
        # Import any other modules you need
    except ImportError as e:
        print(f"Error importing modules from src: {e}")
        traceback.print_exc()
        return

    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})  # Allow requests from any origin
    sock = Sock(app)

    # 控制台输出队列
    # Queue for console output
    console_queue = queue.Queue()

    # 控制台输出捕获器
    # Capture stdout/stderr
    class ConsoleCapture:
        """
        控制台输出捕获器 - 捕获并转发控制台输出到队列
        Console output capturer - Captures and forwards console output to queue
        """
        def __init__(self):
            self.stdout = sys.stdout
            self.stderr = sys.stderr
            self.output = io.StringIO()
            
        def write(self, text):
            """写入文本并发送到队列 - Write text and send to queue"""
            self.stdout.write(text)
            self.output.write(text)
            if text.strip():  # Only send non-empty lines
                console_queue.put({
                    'level': 'error' if self == sys.stderr else 'info',
                    'message': text.strip()
                })
        
        def flush(self):
            """刷新输出流 - Flush output streams"""
            self.stdout.flush()

    # Redirect stdout/stderr to our capture
    sys.stdout = ConsoleCapture()
    sys.stderr = ConsoleCapture()

    # Replace the default progress handler with our web UI version
    from utils.progress import progress
    progress.handler = WebUIProgressHandler()

    # API endpoints
    @app.route('/api/models', methods=['GET'])
    def get_models():
        """
        获取可用的LLM模型列表
        Return available LLM models
        """
        # 由于模型固定为 GPT-4o，直接返回该模型的信息
        # As the model is fixed to GPT-4o, directly return its information.
        hardcoded_llm_order = [("[openai] gpt-4o", "gpt-4o", "OpenAI")]
        return jsonify({
            "models": hardcoded_llm_order
        })

    @app.route('/api/analysts', methods=['GET'])
    def get_analysts():
        """
        获取可用的分析师代理列表
        Return available analyst agents
        """
        return jsonify({
            "analysts": ANALYST_ORDER
        })

    @app.route('/api/analysis', methods=['POST'])
    def run_analysis():
        """
        运行股票分析
        Run stock analysis
        """
        try:
            data = request.get_json()
            print(f"Request data: {data}")
            
            ticker_list = data.get('tickers', '').split(',')
            selected_analysts = data.get('selectedAnalysts', [])
            # model_name = data.get('modelName')
            
            print(f"Processing analysis for tickers: {ticker_list}")
            print(f"Selected analysts: {selected_analysts}")
            # print(f"Using model: {model_name}")
            
            # Try to run the web-specific analysis function
            result = run_hedge_fund_for_web(
                tickers=ticker_list,
                selected_analysts=selected_analysts,
                # model_name=model_name,
                start_date=data.get('startDate') or None,
                end_date=data.get('endDate') or None,
                # 移除 initialCash 参数，使用默认值 - Remove initialCash parameter, use default value
                # initial_cash=data.get('initialCash', 100000),
            )
            
            print("Analysis completed successfully")
            return jsonify(result)
                
        
        except Exception as e:
            print(f"API error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({"error": str(e)}), 500

    @app.route('/api/backtest', methods=['POST'])
    def run_backtest():
        """
        运行历史数据回测
        Run backtesting on historical data
        """
        try:
            data = request.get_json()
            tickers = data.get('tickers', '').split(',')
            start_date = data.get('startDate')
            end_date = data.get('endDate')
            model_name = data.get('modelName')
            selected_analysts = data.get('selectedAnalysts', [])
            initial_capital = data.get('initialCapital', 100000)
            margin_requirement = data.get('marginRequirement', 0.5)
            is_crypto = data.get('isCrypto', False)
            
            # 处理可选日期 - Handle optional dates
            from datetime import datetime, timedelta
            
            # Default end_date to today if not provided
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Default start_date to 3 months before end_date if not provided
            # For backtesting, we use a longer default period
            if not start_date:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                start_date_obj = end_date_obj - timedelta(days=90)  # 3 months
                start_date = start_date_obj.strftime('%Y-%m-%d')
            
            # 移除了 get_model_info 的调用，model_provider 固定为 OpenAI
            # Removed call to get_model_info, model_provider is fixed to OpenAI.
            # model_info = get_model_info(model_name)
            model_provider = "OpenAI" # model_info.provider.value if model_info else "Unknown"
            
            # 运行回测 - Run backtest
            # Backtester 实例化时不再传递 model_name 和 model_provider
            # model_name and model_provider are no longer passed when instantiating Backtester
            backtester = Backtester(
                agent=run_hedge_fund,
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                # model_name=model_name, # 已移除 (Removed)
                # model_provider=model_provider, # 已移除 (Removed)
                selected_analysts=selected_analysts,
                initial_margin_requirement=margin_requirement,
                # is_crypto=is_crypto # is_crypto 已在 Backtester 中移除 (is_crypto removed in Backtester)
            )
            
            performance_metrics = backtester.run_backtest()
            performance_df = backtester.analyze_performance()
            
            # Convert dataframe to dict for JSON serialization
            performance_data = performance_df.to_dict(orient='records')
            
            return jsonify({
                "metrics": performance_metrics,
                "performance": performance_data
            })
            
        except Exception as e:
            return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

    @app.route('/api/round-table', methods=['POST'])
    def run_round_table():
        """Run a round table discussion for a ticker"""
        try:
            # Import round table module
            from src.round_table.main import run_round_table
            
            data = request.get_json()
            ticker = data.get('ticker')
            model_name = data.get('modelName') # model_name 仍然可以从请求中获取，但主要用于显示或记录，而非选择模型 (model_name can still be fetched from request, but mainly for display/logging, not model selection)
            selected_personas = data.get('selectedPersonas', [])
            
            # 移除了 get_model_info 的调用，model_provider 固定为 OpenAI
            # Removed call to get_model_info, model_provider is fixed to OpenAI.
            # model_info = get_model_info(model_name)
            model_provider = "OpenAI" # model_info.provider.value if model_info else "Unknown"
            
            # Setup analysis data structure for round table
            analysis_data = {
                "tickers": [ticker],
                "analyst_signals": {}
            }
            
            # Run round table
            # 调用 run_round_table 时不再传递 model_name 和 model_provider
            # model_name and model_provider are no longer passed when calling run_round_table
            result = run_round_table(
                data=analysis_data, 
                # model_name=model_name, # 已移除 (Removed)
                # model_provider=model_provider, # 已移除 (Removed)
                show_reasoning=True
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

    @app.route('/api/env', methods=['GET'])
    def get_env_vars():
        """Return relevant environment variables (without exposing sensitive API keys)"""
        return jsonify({
            "openai_api_configured": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic_api_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "groq_api_configured": bool(os.getenv("GROQ_API_KEY")),
            "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
        })

    # WebSocket endpoint for logs
    @sock.route('/ws/logs')
    def logs(ws):
        websocket_clients.append(ws)
        print(f"WebSocket client connected. Total clients: {len(websocket_clients)}")
        
        try:
            # Keep the connection open
            while True:
                message = ws.receive()
                # We don't expect messages from clients, but handle them anyway
                if message:
                    print(f"Received from client: {message}")
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            if ws in websocket_clients:
                websocket_clients.remove(ws)
            print(f"WebSocket client disconnected. Remaining clients: {len(websocket_clients)}")

    print(f"Starting API server at http://{host}:{port}")
    app.run(host=host, port=port, debug=True, use_reloader=False)

def check_node_installed():
    """Check if Node.js and npm are installed."""
    node_installed = False
    npm_installed = False
    
    # Try to find the npm executable relative to the node executable
    npm_paths = [
        "npm",  # Standard PATH lookup
        os.path.join(os.path.dirname(shutil.which("node") or ""), "npm"),  # Same directory as node
        os.path.join(os.path.dirname(shutil.which("node") or ""), "npm.cmd"),  # Windows .cmd file
        r"C:\Program Files\nodejs\npm.cmd",  # Common Windows location
        r"C:\Program Files (x86)\nodejs\npm.cmd",  # Common Windows location (x86)
    ]
    
    try:
        node_version = subprocess.run(
            ["node", "--version"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        if node_version.returncode == 0:
            print(f"Found Node.js {node_version.stdout.strip()}")
            node_installed = True
        else:
            print(f"Node.js check failed with exit code {node_version.returncode}")
            return False
    except FileNotFoundError:
        print("Node.js not found")
        return False
    
    # Try different possible npm paths
    for npm_path in npm_paths:
        if not npm_path:
            continue
            
        try:
            print(f"Trying npm at: {npm_path}")
            npm_version = subprocess.run(
                [npm_path, "--version"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            if npm_version.returncode == 0:
                print(f"Found npm {npm_version.stdout.strip()}")
                npm_installed = True
                # Save the working npm path for future use
                os.environ["NPM_PATH"] = npm_path
                break
        except FileNotFoundError:
            continue
    
    if not npm_installed:
        print("npm not found in standard locations")
        
        # On Windows, try one more approach - look for npm via where command
        if os.name == 'nt':
            try:
                where_npm = subprocess.run(
                    ["where", "npm"], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if where_npm.returncode == 0 and where_npm.stdout.strip():
                    npm_path = where_npm.stdout.strip().split('\n')[0]
                    print(f"Found npm via 'where' command at: {npm_path}")
                    try:
                        npm_version = subprocess.run(
                            [npm_path, "--version"], 
                            capture_output=True, 
                            text=True, 
                            check=False
                        )
                        if npm_version.returncode == 0:
                            print(f"Found npm {npm_version.stdout.strip()}")
                            npm_installed = True
                            os.environ["NPM_PATH"] = npm_path
                    except:
                        pass
            except:
                pass
                
    return node_installed and npm_installed

def install_dependencies():
    """Install npm dependencies for the web UI."""
    print("Installing npm dependencies...")
    npm_cmd = os.environ.get("NPM_PATH", "npm")
    try:
        subprocess.run(
            [npm_cmd, "install"], 
            cwd=WEBUI_DIR, 
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print("Trying to install with --force...")
        subprocess.run(
            [npm_cmd, "install", "--force"], 
            cwd=WEBUI_DIR, 
            check=True
        )

def dev_server(host=DEFAULT_HOST, port=DEFAULT_PORT, open_browser=True):
    """Run the Next.js development server."""
    # Check if the directory exists
    if not os.path.exists(WEBUI_DIR):
        print(f"Web UI directory not found at {WEBUI_DIR}")
        print("Creating directory structure...")
        os.makedirs(WEBUI_DIR, exist_ok=True)
        
        # Copy files from a template or warn the user
        print("Please run the setup first with --setup flag")
        return
    
    # Make sure dependencies are installed
    if not os.path.exists(os.path.join(WEBUI_DIR, "node_modules")):
        install_dependencies()
    
    # Create a .env.local file with the API URL
    with open(os.path.join(WEBUI_DIR, ".env.local"), "w") as f:
        f.write(f"NEXT_PUBLIC_API_URL=http://{host}:{API_PORT}\n")
    
    # Copy .env file for web UI access
    copy_env_file()
    
    # Start the dev server
    print(f"Starting Next.js dev server on http://{host}:{port}")
    
    # Run the server in a separate thread
    npm_cmd = os.environ.get("NPM_PATH", "npm")
    server_process = subprocess.Popen(
        [npm_cmd, "run", "dev", "--", "--port", str(port), "--hostname", host],
        cwd=WEBUI_DIR
    )
    
    # Give it a moment to start up
    time.sleep(2)
    
    # Open the browser if requested
    if open_browser:
        webbrowser.open(f"http://{host}:{port}")
    
    try:
        # Keep running until the user interrupts
        server_process.wait()
    except KeyboardInterrupt:
        # Handle clean shutdown on Ctrl+C
        print("\nShutting down dev server...")
        server_process.terminate()
        server_process.wait()

def build_production():
    """Build the Next.js app for production."""
    print("Building production version...")
    npm_cmd = os.environ.get("NPM_PATH", "npm")
    subprocess.run(
        [npm_cmd, "run", "build"], 
        cwd=WEBUI_DIR, 
        check=True
    )
    print("Production build created!")

def setup_webui():
    """Set up the web UI directory structure and initial files."""
    # Create the webui directory if it doesn't exist
    os.makedirs(WEBUI_DIR, exist_ok=True)
    
    # Create various subdirectories
    os.makedirs(os.path.join(WEBUI_DIR, "src", "pages"), exist_ok=True)
    os.makedirs(os.path.join(WEBUI_DIR, "src", "components"), exist_ok=True)
    os.makedirs(os.path.join(WEBUI_DIR, "src", "theme"), exist_ok=True)
    os.makedirs(os.path.join(WEBUI_DIR, "src", "styles"), exist_ok=True)
    os.makedirs(os.path.join(WEBUI_DIR, "public"), exist_ok=True)
    
    # Copy .env file for web UI access
    copy_env_file()
    
    # Create a basic package.json if it doesn't exist
    if not os.path.exists(os.path.join(WEBUI_DIR, "package.json")):
        with open(os.path.join(WEBUI_DIR, "package.json"), "w") as f:
            json.dump({
                "name": "hedge-fund-ai-webui",
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "lint": "next lint"
                },
                "dependencies": {
                    "@emotion/react": "^11.11.1",
                    "@emotion/styled": "^11.11.0",
                    "@mui/icons-material": "^5.14.16",
                    "@mui/material": "^5.14.16",
                    "axios": "^1.6.0",
                    "chart.js": "^4.4.0",
                    "framer-motion": "^10.16.4",
                    "next": "14.0.1",
                    "react": "^18.2.0",
                    "react-chartjs-2": "^5.2.0",
                    "react-dom": "^18.2.0",
                    "react-syntax-highlighter": "^15.5.0",
                    "recharts": "^2.9.2",
                    "notistack": "^3.0.1"
                },
                "devDependencies": {
                    "@types/node": "^20.8.10",
                    "@types/react": "^18.2.35",
                    "@types/react-dom": "^18.2.14",
                    "autoprefixer": "^10.4.16",
                    "eslint": "^8.53.0",
                    "eslint-config-next": "14.0.1",
                    "postcss": "^8.4.31",
                    "tailwindcss": "^3.3.5",
                    "typescript": "^5.2.2"
                },
                "description": "A modern web interface for the AI-driven hedge fund analysis tool.",
                "main": "index.js",
                "keywords": [],
                "author": "",
                "license": "ISC"
            }, f, indent=2)
    
    # Create a basic globals.css if it doesn't exist
    if not os.path.exists(os.path.join(WEBUI_DIR, "src", "styles", "globals.css")):
        with open(os.path.join(WEBUI_DIR, "src", "styles", "globals.css"), "w") as f:
            f.write("""
html,
body {
  padding: 0;
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen,
    Ubuntu, Cantarell, Fira Sans, Droid Sans, Helvetica Neue, sans-serif;
}

* {
  box-sizing: border-box;
}

a {
  color: inherit;
  text-decoration: none;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.MuiPopover-paper {
  border-radius: 8px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
}

.chart-container {
  border-radius: 8px;
  overflow: hidden;
}

.card-hover {
  transition: all 0.2s ease;
}

.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.gradient-text {
  background: linear-gradient(90deg, #3f8cff 0%, #6ba7ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-fill-color: transparent;
}
        """.strip())
    
    print(f"Web UI template set up in {WEBUI_DIR}")
    print("Run with --dev to start the development server")

def run_hedge_fund_for_web(tickers, selected_analysts, start_date=None, end_date=None, initial_cash=100000):
    """
    Special version of run_hedge_fund optimized for web UI integration.
    This bypasses some of the CLI-specific code and analyst selection logic.
    """
    # Import necessary modules
    from src.main import create_workflow # create_workflow 可能不再需要，如果直接调用 run_hedge_fund (create_workflow might not be needed if run_hedge_fund is called directly)
    from src.graph.state import AgentState, show_agent_reasoning # show_agent_reasoning 可能不再需要 (show_agent_reasoning might not be needed)
    # 移除了 get_model_info 的导入 (Removed import of get_model_info)
    # from src.llm.models import get_model_info 
    init(autoreset=True)  # Initialize colorama
    
    # Import progress tracker from the correct location
    try:
        from src.utils.progress import progress
    except ImportError:
        from utils.progress import progress
    
    # Initialize progress
    try:
        progress.start()
    except:
        # Fallback if no start method exists
        pass
        
    broadcast_log("Starting analysis process", "info")
    
    # 移除了 get_model_info 的调用，model_provider 固定为 OpenAI
    # Removed call to get_model_info, model_provider is fixed to OpenAI.
    # model_info = get_model_info(model_name)
    model_provider = "OpenAI" # model_info.provider.value if model_info else "Unknown"
    # 固定使用 GPT-4o 模型 - Fixed to use GPT-4o model
    model_name = "gpt-4o"
    # broadcast_log(f"Using model: {model_name} ({model_provider})", "info") 
    
    # Create portfolio
    portfolio = {
        "cash": initial_cash,
        "positions": {},
        "cost_basis": {}, 
        "realized_gains": {ticker: {"long": 0.0, "short": 0.0} for ticker in tickers}
    }
    
    # Create initial state
    initial_state = {
        "messages": [],
        "data": {
            "tickers": tickers,
            "portfolio": portfolio,
            "start_date": start_date if start_date else (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": end_date if end_date else datetime.now().strftime("%Y-%m-%d"),
            "analyst_signals": {},
            # "is_crypto": is_crypto # is_crypto 已移除 (is_crypto removed)
        },
        "metadata": {
            "show_reasoning": True,
            "model_name": model_name, # 用于元数据 (For metadata)
            "model_provider": model_provider # 用于元数据 (For metadata)
        }
    }
    
    broadcast_log(f"Analyzing tickers: {tickers}", "info")
    broadcast_log(f"Using analysts: {selected_analysts}", "info")
    
    # Process each analyst manually to bypass the workflow issues
    from src.agents.warren_buffett import warren_buffett_agent
    from src.agents.bill_ackman import bill_ackman_agent
    from src.agents.ben_graham import ben_graham_agent
    from src.agents.charlie_munger import charlie_munger_agent
    from src.agents.cathie_wood import cathie_wood_agent
    from src.agents.peter_lynch import peter_lynch_agent
    from src.agents.portfolio_manager import portfolio_management_agent
    
    # Map of available agents
    agent_map = {
        "warren_buffett_agent": warren_buffett_agent,
        "bill_ackman_agent": bill_ackman_agent,
        "ben_graham_agent": ben_graham_agent,
        "charlie_munger_agent": charlie_munger_agent,
        "cathie_wood_agent": cathie_wood_agent,
        "peter_lynch_agent": peter_lynch_agent,
        "portfolio_management_agent": portfolio_management_agent
    }
    
    # Current state
    state = initial_state
    
    # 运行每个选定的分析师
    for analyst_name in selected_analysts:
        if analyst_name in agent_map:
            broadcast_log(f"Running analyst: {analyst_name}", "info")
            try:
                agent_fn = agent_map[analyst_name]
                result = agent_fn(AgentState(state))
                
                if result:
                    # Update state with results
                    if "messages" in result:
                        state["messages"] = result["messages"]
                    if "data" in result:
                        state["data"] = result["data"]
                    
                
                broadcast_log(f"Completed {analyst_name} analysis", "success")
            except Exception as e:
                broadcast_log(f"Error in {analyst_name}: {str(e)}", "error")
                broadcast_log(traceback.format_exc(), "error")
    
    # 准备最终输出 - 新的数组格式
    # Prepare the final output - new array format
    result = {
        "ticker_analyses": {}
    }
    
    # 从state中获取分析结果并转换为新格式
    analyst_signals = state["data"].get("analyst_signals", {})

    
    for ticker in tickers:
        result["ticker_analyses"][ticker] = []
        
        # 为每个选定的分析师创建一个结果对象
        # Create a result object for each selected analyst
        for analyst_name in selected_analysts:
            analyst_result = {
                "agent_name": analyst_name,
                "signal": "中性",  # 默认信号
                "confidence": 50.0,  # 默认置信度
                "reasoning": "分析正在进行中..."  # 默认推理
            }
            
            # 如果有实际的分析结果，使用它们
            # If there are actual analysis results, use them
            if analyst_name in analyst_signals and ticker in analyst_signals[analyst_name]:
                analyst_data = analyst_signals[analyst_name][ticker]
                
                # 直接从分析师信号中获取数据
                # Get data directly from analyst signals
                if "signal" in analyst_data:
                    analyst_result["signal"] = analyst_data["signal"]
                
                if "confidence" in analyst_data:
                    analyst_result["confidence"] = analyst_data["confidence"]
                
                if "reasoning" in analyst_data:
                    analyst_result["reasoning"] = analyst_data["reasoning"]
            
            result["ticker_analyses"][ticker].append(analyst_result)
    
    broadcast_log("Analysis completed successfully", "success")
    
    return result

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Hedge Fund AI Web UI")
    parser.add_argument("--dev", action="store_true", help="Start the development server")
    parser.add_argument("--build", action="store_true", help="Build for production")
    parser.add_argument("--setup", action="store_true", help="Set up the web UI")
    parser.add_argument("--api", action="store_true", help="Start the API server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port for the web server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host for the web server")
    parser.add_argument("--api-port", type=int, default=API_PORT, help="Port for the API server")
    
    args = parser.parse_args()
    
    # Check if Node.js is installed for web UI functions
    if args.dev or args.build or args.setup:
        if not check_node_installed():
            print("Node.js and npm are required to run the web UI.")
            print("Please install Node.js from https://nodejs.org/")
            return 1
    
    # Setup the web UI if requested
    if args.setup:
        setup_webui()
        return 0
    
    # Start the API server in a separate thread
    api_thread = None
    if args.api or args.dev:
        api_thread = threading.Thread(
            target=start_api_server,
            kwargs={"host": args.host, "port": args.api_port}
        )
        api_thread.daemon = True
        api_thread.start()
    
    # Start the development server if requested
    if args.dev:
        dev_server(host=args.host, port=args.port)
        return 0
    
    # Build for production if requested
    if args.build:
        build_production()
        return 0
    
    # If only API server was requested, keep it running
    if args.api and api_thread:
        print("API server running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down API server...")
        return 0
    
    # If no action specified, show help
    if not (args.setup or args.dev or args.build or args.api):
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 