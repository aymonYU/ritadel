# YFinance 访问限制解决方案

本项目实现了一个全面的解决方案来处理 yfinance 的访问限制问题。

## 主要功能

### 1. 智能速率限制
- 自动跟踪每分钟的请求数量
- 当达到限制时自动等待
- 默认限制：每分钟30个请求
- 线程安全设计

### 2. 重试机制
- 自动重试失败的请求（最多3次）
- 指数退避算法，避免立即重试
- 随机延迟，减少被检测的可能性

### 3. 用户代理轮换
- 随机选择不同的浏览器用户代理
- 模拟真实的浏览器访问
- 减少被识别为机器的可能性

### 4. 代理支持
- 支持HTTP和HTTPS代理
- 通过环境变量配置
- 进一步隐藏请求来源

### 5. 会话管理
- 使用持久连接
- 自动处理连接池
- 优化网络性能

## 使用方法

### 基本使用
代码会自动应用速率限制，无需额外配置：

```python
from tools.api import get_prices, get_financial_metrics

# 这些函数现在会自动使用速率限制
prices = get_prices("AAPL", "2024-01-01", "2024-12-31")
metrics = get_financial_metrics("AAPL", "2024-12-31")
```

### 自定义速率限制
```python
from tools.api import configure_yfinance_rate_limit

# 设置更保守的限制：每分钟20个请求
configure_yfinance_rate_limit(max_requests_per_minute=20)

# 设置更激进的限制：每分钟50个请求（不推荐）
configure_yfinance_rate_limit(max_requests_per_minute=50)
```

### 代理配置
在环境变量中设置代理：

```bash
# HTTP代理
export YFINANCE_PROXY_HTTP="http://proxy.example.com:8080"

# HTTPS代理  
export YFINANCE_PROXY_HTTPS="https://proxy.example.com:8080"

# 带认证的代理
export YFINANCE_PROXY_HTTP="http://username:password@proxy.example.com:8080"
```

或在代码中设置：

```python
import os
os.environ["YFINANCE_PROXY_HTTP"] = "http://proxy.example.com:8080"
os.environ["YFINANCE_PROXY_HTTPS"] = "https://proxy.example.com:8080"
```

## 多数据源回退策略

当 Yahoo Finance 不可用时，系统会自动回退到其他数据源：

1. **Yahoo Finance** (主要源) - 使用速率限制和重试
2. **StockData.org** - 第一备用源
3. **Alpha Vantage** - 最后备用源

## 缓存机制

所有数据都会被缓存，减少重复请求：
- 价格数据缓存
- 财务指标缓存  
- 新闻数据缓存
- 内部交易数据缓存

## 监控和调试

### 日志输出
系统会输出有用的调试信息：

```
Rate limit reached, waiting 15.2 seconds...
YFinance request attempt 1 failed for AAPL: Request timeout
Using proxy configuration: {'http': 'http://proxy.example.com:8080'}
```

### 性能优化建议

1. **合理设置速率限制**
   - 开发环境：20-30请求/分钟
   - 生产环境：15-25请求/分钟
   - 大量数据处理：10-20请求/分钟

2. **利用缓存**
   - 避免重复请求相同数据
   - 缓存会自动处理日期范围过滤

3. **批量处理**
   - 尽可能批量获取数据
   - 避免频繁的单个股票查询

4. **错误处理**
   - 系统会自动重试和回退
   - 监控日志以识别问题

## 环境变量配置

```bash
# API密钥
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"
export STOCKDATA_API_KEY="your_stockdata_key"
export FINNHUB_API_KEY="your_finnhub_key"
export EODHD_API_KEY="your_eodhd_key"

# 代理设置（可选）
export YFINANCE_PROXY_HTTP="http://proxy.example.com:8080"
export YFINANCE_PROXY_HTTPS="https://proxy.example.com:8080"
```

## 故障排除

### 常见问题

1. **仍然被限制访问**
   - 降低速率限制设置
   - 使用代理服务器
   - 检查网络连接

2. **代理连接失败**
   - 验证代理服务器地址和端口
   - 检查代理认证信息
   - 测试代理连接

3. **数据获取失败**
   - 检查API密钥配置
   - 验证股票代码正确性
   - 查看错误日志

### 联系支持
如果问题持续存在，请检查：
- 网络连接状态
- API密钥有效性  
- 防火墙设置
- 代理配置

这个解决方案应该能显著减少 yfinance 访问限制的问题，同时提供多重备份机制确保数据获取的可靠性。 