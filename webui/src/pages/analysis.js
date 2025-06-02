import { useState, useEffect } from 'react';
import { Box, Grid, Typography, Card, CardContent, TextField, Button, Autocomplete, Checkbox, Chip, FormControlLabel, FormGroup, Divider, Stepper, Step, StepLabel, StepContent, Paper, LinearProgress, Alert, Fade, Slide, IconButton, Tooltip, Avatar, CardActionArea, useTheme } from '@mui/material';
import { Search as SearchIcon, Send as SendIcon, Check as CheckIcon, TrendingUp, TrendingDown, AccountBalance, Rocket, Analytics, Person, Add, Remove } from '@mui/icons-material';
import { runAnalysis } from '../utils/api';

// 添加自定义CSS动画
const customStyles = `
  @keyframes pulse {
    0% {
      transform: scale(1);
      opacity: 0.8;
    }
    50% {
      transform: scale(1.1);
      opacity: 0.4;
    }
    100% {
      transform: scale(1);
      opacity: 0.8;
    }
  }

  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes shimmer {
    0% {
      background-position: -200px 0;
    }
    100% {
      background-position: calc(200px + 100%) 0;
    }
  }

  @keyframes float {
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-10px);
    }
  }

  .shimmer-effect {
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    background-size: 200px 100%;
    animation: shimmer 2s infinite;
  }

  .float-animation {
    animation: float 3s ease-in-out infinite;
  }
`;

// 注入自定义样式
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = customStyles;
  document.head.appendChild(styleElement);
}

// Sample data
const modelOptions = [
  { label: '[anthropic] claude-3.5-sonnet', value: 'claude-3-5-sonnet-latest' },
  { label: '[anthropic] claude-3.7-sonnet', value: 'claude-3-7-sonnet-latest' },
  { label: '[groq] deepseek-r1 70b', value: 'deepseek-r1-distill-llama-70b' },
  { label: '[groq] llama-3.3 70b', value: 'llama-3.3-70b-versatile' },
  { label: '[openai] gpt-4o', value: 'gpt-4o' },
  { label: '[openai] gpt-4o-mini', value: 'gpt-4o-mini' },
  { label: '[openai] o1', value: 'o1' },
  { label: '[openai] o3-mini', value: 'o3-mini' },
  { label: '[gemini] gemini-2.0-flash', value: 'gemini-2.0-flash' },
];

// 分析师分类数据
const analystCategories = {
  growth: {
    title: '成长股分析师',
    icon: <Rocket sx={{ fontSize: 20 }} />,
    color: '#f06292',
    description: '专注于高增长潜力和创新型公司',
    analysts: [
      { label: 'Cathie Wood (木头姐)', value: 'cathie_wood_agent', description: '专注于颠覆性创新和高速增长的技术公司', avatar: '🚀' },
      { label: 'Phil Fisher (菲尔·费舍尔)', value: 'phil_fisher_agent', description: '识别具有强大竞争优势和增长潜力的公司', avatar: '📈' },
      { label: 'Bill Ackman (艾克曼)', value: 'bill_ackman_agent', description: '识别具有长期增长和激进潜力的优质企业', avatar: '💎' },
    ]
  },
  value: {
    title: '价值股分析师',
    icon: <AccountBalance sx={{ fontSize: 20 }} />,
    color: '#e91e63',
    description: '专注于被低估的优质企业和稳健投资',
    analysts: [
      { label: 'Warren Buffett (巴菲特)', value: 'warren_buffett_agent', description: '分析具有强大基本面和合理价格的优质企业', avatar: '🎯' },
      { label: 'Charlie Munger (芒格)', value: 'charlie_munger_agent', description: '使用心理模型评估公司，并考虑护城河和管理质量', avatar: '🧠' },
      { label: 'Ben Graham (格雷厄姆)', value: 'ben_graham_agent', description: '专注于深度价值股票，交易价格低于内在价值，具有安全边际', avatar: '📊' },
      { label: 'Peter Lynch (彼得·林奇)', value: 'peter_lynch_agent', description: '专注于具有强大基本面和增长潜力的公司', avatar: '🔍' },
    ]
  }
};

// 将原来的 analystOptions 转换为扁平数组以保持兼容性
const analystOptions = [
  ...analystCategories.growth.analysts,
  ...analystCategories.value.analysts
];

// 股票代码建议
const stockSuggestions = [
  { symbol: '0700.HK', name: '腾讯', category: '科技' },
  { symbol: 'AAPL', name: '苹果', category: '科技' },
  { symbol: 'MSFT', name: '微软', category: '科技' },
  { symbol: '09988.HK', name: '阿里巴巴', category: '科技' },
  { symbol: '03690.HK', name: '美团', category: '科技' },
  { symbol: '01810.HK', name: '小米', category: '科技' },
  { symbol: '00001.HK', name: '长和', category: '金融' },
  { symbol: '00005.HK', name: '汇丰控股', category: '金融' },
  { symbol: '00006.HK', name: '电能实业', category: '金融' },
  { symbol: '600519.SS', name: '贵州茅台', category: '消费品' },
  { symbol: '601888.SS', name: '中国中免', category: '消费品' },
  { symbol: '601318.SS', name: '中国平安', category: '金融' },
  { symbol: '601398.SS', name: '工商银行', category: '金融' },
  { symbol: '601939.SS', name: '建设银行', category: '金融' },
  { symbol: 'GOOGL', name: '谷歌', category: '科技' },
  { symbol: 'AMZN', name: '亚马逊', category: '科技' },
  { symbol: 'TSLA', name: '特斯拉', category: '汽车' },
  { symbol: 'META', name: 'Meta', category: '科技' },
  { symbol: 'NVDA', name: '英伟达', category: '科技' },
  { symbol: 'NFLX', name: '奈飞', category: '娱乐' },
  { symbol: 'BABA', name: '阿里巴巴', category: '科技' },
  { symbol: 'TSM', name: '台积电', category: '半导体' },
  { symbol: 'V', name: 'Visa', category: '金融' },
  { symbol: 'JPM', name: '摩根大通', category: '金融' },
  { symbol: 'JNJ', name: '强生', category: '医疗' },
  { symbol: 'WMT', name: '沃尔玛', category: '零售' },
  { symbol: 'PG', name: '宝洁', category: '消费品' },
  { symbol: 'UNH', name: '联合健康', category: '医疗' },
  { symbol: 'HD', name: '家得宝', category: '零售' },
  { symbol: 'MA', name: '万事达', category: '金融' },
  { symbol: 'DIS', name: '迪士尼', category: '娱乐' },
  { symbol: 'PYPL', name: 'PayPal', category: '金融' },
  { symbol: 'ADBE', name: 'Adobe', category: '科技' },
  { symbol: 'CRM', name: 'Salesforce', category: '科技' },
  { symbol: 'ORCL', name: '甲骨文', category: '科技' },
  { symbol: 'INTC', name: '英特尔', category: '半导体' },
  { symbol: 'AMD', name: 'AMD', category: '半导体' },
  { symbol: 'QCOM', name: '高通', category: '半导体' }
];

// 按分类分组股票建议
const groupedStockSuggestions = stockSuggestions.reduce((acc, stock) => {
  if (!acc[stock.category]) {
    acc[stock.category] = [];
  }
  acc[stock.category].push(stock);
  return acc;
}, {});

// 分类颜色映射
const categoryColors = {
  '科技': '#f06292',
  '金融': '#4caf50',
  '医疗': '#ff7043',
  '汽车': '#ff9800',
  '娱乐': '#ba68c8',
  '零售': '#795548',
  '消费品': '#607d8b',
  '半导体': '#e91e63'
};

export default function Analysis() {
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';

  const [activeStep, setActiveStep] = useState(0);
  const [tickers, setTickers] = useState('');
  const [selectedAnalysts, setSelectedAnalysts] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [progress, setProgress] = useState({});
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isFormValid, setIsFormValid] = useState(false);
  const [tickerInputFocused, setTickerInputFocused] = useState(false);

  // 根据主题模式获取适应的颜色
  const getThemeColors = () => {
    if (isDarkMode) {
      return {
        primary: '#e91e63',
        secondary: '#f06292',
        accent: '#f48fb1',
        backgroundGradient: 'linear-gradient(135deg, #880e4f 0%, #e91e63 100%)',
        cardBackground: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        inputBackground: 'rgba(51, 65, 85, 0.95)',
        textPrimary: '#ffffff',
        textSecondary: '#cbd5e1',
        shimmerColor: 'rgba(255,255,255,0.1)'
      };
    } else {
      return {
        primary: '#e91e63',
        secondary: '#f06292',
        accent: '#f48fb1',
        backgroundGradient: '#e91e63',
        cardBackground: '#ffffff',
        inputBackground: 'rgba(255,255,255,0.95)',
        textPrimary: '#ffffff',
        textSecondary: '#666666',
        shimmerColor: 'rgba(255,255,255,0.3)'
      };
    }
  };

  const colors = getThemeColors();

  useEffect(() => {
    let valid = false;

    // Step-specific validation
    switch (activeStep) {
      case 0: // Select Stocks step
        // For the first step, ticker is required and should not exceed 3 stocks
        const currentTickerList = parseTickerInput(tickers);
        valid = tickers.trim() !== '' && currentTickerList.length <= 3;
        break;

      case 1: // Choose Analysts step
        // For the second step, at least one analyst must be selected
        valid = selectedAnalysts.length > 0;
        break;

      default:
        valid = false;
    }

    setIsFormValid(valid);
  }, [activeStep, tickers, selectedAnalysts]);

  const handleNext = () => {
    // Skip full validation during intermediate steps
    // We only need to validate the current step's fields

    // For first step, check ticker input and count
    if (activeStep === 0) {
      if (!tickers.trim()) {
        setAnalysisError("请输入至少一个股票代码");
        return;
      }
      
      const currentTickerList = parseTickerInput(tickers);
      if (currentTickerList.length > 3) {
        setAnalysisError("请节省一点token消化，最多选择3个股票");
        return;
      }
    }

    // For second step, check analyst selection
    else if (activeStep === 1) {
      if (selectedAnalysts.length === 0) {
        setAnalysisError("请选择至少一个分析师");
        return;
      }
    }

    // Clear any previous errors
    setAnalysisError(null);
    // Move to next step
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
  };

  // 处理分析师选择
  const handleAnalystToggle = (analyst) => {
    const isSelected = selectedAnalysts.some(a => a.value === analyst.value);
    if (isSelected) {
      setSelectedAnalysts(selectedAnalysts.filter(a => a.value !== analyst.value));
    } else {
      setSelectedAnalysts([...selectedAnalysts, analyst]);
    }
  };

  // 处理分类全选
  const handleCategorySelectAll = (category) => {
    const categoryAnalysts = analystCategories[category].analysts;
    const allSelected = categoryAnalysts.every(analyst =>
      selectedAnalysts.some(selected => selected.value === analyst.value)
    );

    if (allSelected) {
      // 取消选择该分类的所有分析师
      setSelectedAnalysts(selectedAnalysts.filter(selected =>
        !categoryAnalysts.some(analyst => analyst.value === selected.value)
      ));
    } else {
      // 选择该分类的所有分析师
      const newAnalysts = categoryAnalysts.filter(analyst =>
        !selectedAnalysts.some(selected => selected.value === analyst.value)
      );
      setSelectedAnalysts([...selectedAnalysts, ...newAnalysts]);
    }
  };

  // 解析输入的股票代码
  const parseTickerInput = (input) => {
    return input.split(/[,\s]+/).filter(t => t.trim() !== '').map(t => t.trim().toUpperCase());
  };

  const currentTickers = parseTickerInput(tickers);

  const handleStartAnalysis = () => {
    if (validateInputs()) {
      setIsAnalyzing(true);
      setAnalysisError(null);

      // Log the request details to console
      console.log("Starting analysis:", {
        tickers: tickers,
        analysts: selectedAnalysts.map(a => a.value)
      });

      // Show progress immediately
      const ticker_list = tickers.split(',').map(t => t.trim());
      const initialProgress = {};
      selectedAnalysts.forEach(analyst => {
        initialProgress[analyst.value] = {};
        ticker_list.forEach(ticker => {
          initialProgress[analyst.value][ticker] = {
            status: '开始分析...',
            percent: 10
          };
        });
      });
      setProgress(initialProgress);

      // Make API request with fetch directly instead of axios for debugging
      fetch('http://127.0.0.1:5000/api/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tickers: tickers,
          selectedAnalysts: selectedAnalysts.map(a => a.value),
        })
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('Analysis success:', data);

          // Use a timeout to ensure we can see results
          setTimeout(() => {
            setIsAnalyzing(false);

            if (data && data.ticker_analyses) {
              // 直接使用API返回的数据，不进行格式转换
              // Use API response data directly without format conversion
              setAnalysisResults(data);
            } else {
              // Create fallback data in the new array format
              const fallbackData = {
                ticker_analyses: {}
              };

              const ticker_list = tickers.split(',').map(t => t.trim());
              ticker_list.forEach(ticker => {
                fallbackData.ticker_analyses[ticker] = selectedAnalysts.map(analyst => ({
                  agent_name: analyst.value,
                  signal: Math.random() > 0.5 ? '买入' : '卖出',
                  confidence: Math.round(Math.random() * 40 + 60), // 60-100
                  reasoning: `${analyst.label} 对 ${ticker} 的回退分析`
                }));
              });

              setAnalysisResults(fallbackData);
            }

            setActiveStep(2); // Move to results step
          }, 3000);
        })
        .catch(error => {
          console.error('Analysis error:', error);

          // Don't hide the progress view, just show the error
          setAnalysisError(`错误：${error.message}。请查看控制台获取详细信息。`);

          // Create fake/fallback results after error for testing
          setTimeout(() => {
            const fallbackResults = {
              tickers: ticker_list,
              date: new Date().toISOString().split('T')[0],
              signals: {}
            };

            ticker_list.forEach(ticker => {
              fallbackResults.signals[ticker] = {
                overallSignal: '中性',
                confidence: 50,
                analysts: selectedAnalysts.map(analyst => ({
                  name: analyst.label,
                  signal: '中性',
                  confidence: 50,
                  reasoning: `错误回退：${analyst.label} 对 ${ticker} 的分析`
                }))
              };
            });

            setIsAnalyzing(false);
            setAnalysisResults(fallbackResults);
            setActiveStep(2);
          }, 5000);
        });
    }
  };

  const handleSelectAllAnalysts = () => {
    if (selectedAnalysts.length === analystOptions.length) {
      setSelectedAnalysts([]);
    } else {
      setSelectedAnalysts([...analystOptions]);
    }
  };

  const validateInputs = () => {
    if (!tickers.trim()) {
      setAnalysisError("请输入至少一个股票代码");
      return false;
    }

    const currentTickerList = parseTickerInput(tickers);
    if (currentTickerList.length > 3) {
      setAnalysisError("请节省一点token消化，最多选择3个股票");
      return false;
    }

    if (selectedAnalysts.length === 0) {
      setAnalysisError("请选择至少一个分析师");
      return false;
    }

    return true;
  };

  const getDefaultDates = () => {
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);

    return {
      endDate: today.toISOString().split('T')[0],  // YYYY-MM-DD format
      startDate: thirtyDaysAgo.toISOString().split('T')[0]
    };
  };

  const defaults = getDefaultDates();

  const steps = [
    {
      label: '输入股票代码',
      description: '输入您想要分析的股票代码（最多3个）',
      content: (
        <Fade in timeout={800}>
          <Box sx={{ mt: 2 }}>
            {/* 股票代码输入区域 */}
            <Box sx={{
              position: 'relative',
              background: colors.primary,
              borderRadius: 2,
              p: 3,
              mb: 3,
              color: colors.textPrimary,
              overflow: 'hidden'
            }}>
              {/* 背景装饰 */}
              <Box sx={{
                position: 'absolute',
                top: -20,
                right: -20,
                width: 100,
                height: 100,
                borderRadius: '50%',
                background: colors.shimmerColor,
                animation: 'pulse 2s infinite'
              }} />

              <Box sx={{
                position: 'absolute',
                bottom: -30,
                left: -30,
                width: 80,
                height: 80,
                borderRadius: '50%',
                background: isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.1)',
                animation: 'float 4s ease-in-out infinite reverse'
              }} />

              <Typography variant="h6" gutterBottom sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                position: 'relative',
                zIndex: 1,
                color: colors.textPrimary
              }}>
                <TrendingUp />
                股票代码输入
              </Typography>

              <TextField
                label=""
                fullWidth
                margin="normal"
                placeholder="例如: AAPL, MSFT, GOOGL"
                value={tickers}
                onChange={(e) => setTickers(e.target.value)}
                onFocus={() => setTickerInputFocused(true)}
                onBlur={() => setTickerInputFocused(false)}
                helperText="输入股票代码，用逗号或空格分隔（最多3个）"
                InputProps={{
                  sx: {
                    bgcolor: colors.inputBackground,
                    borderRadius: 2,
                    position: 'relative',
                    zIndex: 1,
                    transition: 'all 0.3s',
                    '& .MuiInputBase-input': {
                      color: isDarkMode ? theme.palette.text.primary : '#333',
                      fontSize: '1.1rem',
                      fontWeight: '500'
                    },
                    '&:hover': {
                      bgcolor: isDarkMode ? 'rgba(45, 55, 72, 1)' : 'rgba(255,255,255,1)',
                      transform: 'translateY(-1px)',
                      boxShadow: `0 4px 12px ${isDarkMode ? 'rgba(102, 126, 234, 0.3)' : 'rgba(0,0,0,0.15)'}`
                    },
                    '&.Mui-focused': {
                      bgcolor: isDarkMode ? 'rgba(45, 55, 72, 1)' : 'rgba(255,255,255,1)',
                      transform: 'translateY(-2px)',
                      boxShadow: `0 6px 20px ${isDarkMode ? 'rgba(102, 126, 234, 0.4)' : 'rgba(0,0,0,0.2)'}`
                    }
                  }
                }}
                InputLabelProps={{
                  sx: {
                    color: isDarkMode ? theme.palette.text.secondary : '#333',
                    fontWeight: '500',
                    '&.Mui-focused': {
                      color: colors.primary
                    }
                  }
                }}
                FormHelperTextProps={{
                  sx: {
                    color: isDarkMode ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.9)',
                    fontWeight: '400',
                    position: 'relative',
                    zIndex: 1
                  }
                }}
              />
            </Box>

            {/* 股票数量限制提示 */}
            {currentTickers.length > 0 && (
              <Slide direction="up" in timeout={300}>
                <Box sx={{ mb: 2 }}>
                  <Alert 
                    severity={currentTickers.length > 3 ? "error" : currentTickers.length === 3 ? "warning" : "info"}
                    sx={{ 
                      borderRadius: 2,
                      '& .MuiAlert-message': {
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1
                      }
                    }}
                  >
                    {currentTickers.length > 3 ? (
                      <>
                        <strong>请节省一点token消化！</strong> 最多只能选择3个股票，当前已选择 {currentTickers.length} 个
                      </>
                    ) : currentTickers.length === 3 ? (
                      <>
                        已达到最大选择数量（3个股票）
                      </>
                    ) : (
                      <>
                        已选择 {currentTickers.length} 个股票，还可以选择 {3 - currentTickers.length} 个
                      </>
                    )}
                  </Alert>
                </Box>
              </Slide>
            )}

            {/* 当前输入的股票代码展示 */}
            {currentTickers.length > 0 && (
              <Slide direction="up" in timeout={500}>
                <Box sx={{ mb: 3 }}>
                  <Box sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    mb: 2
                  }}>
                    <Typography variant="subtitle2" sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      fontWeight: 'bold'
                    }}>
                      <Box sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: currentTickers.length > 3 ? 'error.main' : 'primary.main',
                        animation: 'pulse 2s infinite'
                      }} />
                      已输入股票 ({currentTickers.length}/3 个)
                    </Typography>
                    <Button
                      size="small"
                      color="error"
                      variant="outlined"
                      onClick={() => setTickers('')}
                      sx={{
                        minWidth: 'auto',
                        px: 2,
                        fontSize: '0.75rem'
                      }}
                    >
                      清空
                    </Button>
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {currentTickers.map((ticker, index) => {
                      const stockInfo = stockSuggestions.find(s => s.symbol === ticker);
                      const isOverLimit = index >= 3;
                      return (
                        <Fade in timeout={300 + index * 100} key={ticker}>
                          <Chip
                            label={stockInfo ? `${ticker} ${stockInfo.name}` : ticker}
                            color={isOverLimit ? "error" : "primary"}
                            variant="filled"
                            onDelete={() => {
                              const newTickers = currentTickers.filter(t => t !== ticker);
                              setTickers(newTickers.join(', '));
                            }}
                            sx={{
                              fontWeight: 'bold',
                              fontSize: '0.875rem',
                              height: 32,
                              animation: 'fadeInUp 0.5s ease-out',
                              animationDelay: `${index * 0.1}s`,
                              animationFillMode: 'both',
                              background: isOverLimit ? 
                                'linear-gradient(135deg, #f4433620, #f4433640)' :
                                (stockInfo ?
                                  `linear-gradient(135deg, ${categoryColors[stockInfo.category]}20, ${categoryColors[stockInfo.category]}40)` :
                                  'linear-gradient(135deg, #2196f320, #2196f340)'),
                              border: isOverLimit ?
                                '1px solid #f4433660' :
                                (stockInfo ?
                                  `1px solid ${categoryColors[stockInfo.category]}60` :
                                  '1px solid #2196f360'),
                              transition: 'all 0.3s',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                boxShadow: 3,
                                background: isOverLimit ?
                                  'linear-gradient(135deg, #f4433630, #f4433650)' :
                                  (stockInfo ?
                                    `linear-gradient(135deg, ${categoryColors[stockInfo.category]}30, ${categoryColors[stockInfo.category]}50)` :
                                    'linear-gradient(135deg, #2196f330, #2196f350)'),
                              },
                              '& .MuiChip-deleteIcon': {
                                color: isOverLimit ? '#f44336' : (stockInfo ? categoryColors[stockInfo.category] : '#2196f3'),
                                '&:hover': {
                                  color: '#f44336'
                                }
                              }
                            }}
                          />
                        </Fade>
                      );
                    })}
                  </Box>
                </Box>
              </Slide>
            )}

            {/* 股票代码建议 */}
            <Box>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Analytics fontSize="small" />
                热门股票建议
                {currentTickers.length >= 3 && (
                  <Chip 
                    label="已达上限" 
                    size="small" 
                    color="warning"
                    sx={{ fontSize: '0.7rem', height: 20 }}
                  />
                )}
              </Typography>

              {/* 按分类展示股票建议 */}
              <Grid container spacing={1}>
                {Object.entries(groupedStockSuggestions).slice(0, 8).map(([category, stocks]) => (
                  <Grid item xs={12} sm={6} md={3} key={category}>
                    <Box sx={{ mb: 2 }}>
                      <Typography
                        variant="caption"
                        sx={{
                          color: categoryColors[category],
                          fontWeight: 'bold',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 0.5,
                          mb: 1
                        }}
                      >
                        <Box
                          sx={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            bgcolor: categoryColors[category]
                          }}
                        />
                        {category}
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                        {stocks.slice(0, 3).map((stock, index) => {
                          const isAlreadySelected = parseTickerInput(tickers).includes(stock.symbol);
                          const isAtLimit = currentTickers.length >= 3;
                          const cannotAdd = isAlreadySelected || isAtLimit;
                          
                          return (
                            <Chip
                              key={stock.symbol}
                              label={`${stock.symbol} ${stock.name}`}
                              size="small"
                              clickable={!cannotAdd}
                              disabled={cannotAdd}
                              onClick={() => {
                                if (!cannotAdd) {
                                  setTickers(prev => (prev ? `${prev}, ${stock.symbol}` : stock.symbol));
                                }
                              }}
                              sx={{
                                fontSize: '0.75rem',
                                height: 24,
                                background: cannotAdd ?
                                  'rgba(255,255,255,0.05)':
                                  `${categoryColors[category]}15`,
                                color: cannotAdd ?
                                  (isDarkMode ? 'grey.400' : 'grey.600') :
                                  categoryColors[category],
                                border: `1px solid ${categoryColors[category]}30`,
                                transition: 'all 0.3s',
                                '&:hover': !cannotAdd ? {
                                  transform: 'translateY(-1px)',
                                  boxShadow: 1,
                                  bgcolor: `${categoryColors[category]}25`,
                                } : {},
                                '&.Mui-disabled': {
                                  opacity: 0.5
                                }
                              }}
                            />
                          );
                        })}
                      </Box>
                    </Box>
                  </Grid>
                ))}
              </Grid>

            </Box>
          </Box>
        </Fade>
      ),
    },
    {
      label: '选择分析师',
      description: '选择不同投资风格的AI分析师',
      content: (
        <Fade in timeout={800}>
          <Box sx={{ mt: 2 }}>
            {/* 总体控制 */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
              <Box>
                <Typography variant="h6" gutterBottom>
                  选择投资分析师
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  已选择 {selectedAnalysts.length} 位分析师
                </Typography>
              </Box>
              <Button
                variant="outlined"
                size="small"
                onClick={handleSelectAllAnalysts}
                startIcon={selectedAnalysts.length === analystOptions.length ? <Remove /> : <Add />}
              >
                {selectedAnalysts.length === analystOptions.length ? '清空选择' : '全部选择'}
              </Button>
            </Box>

            {/* 分析师分类展示 */}
            <Grid container spacing={2}>
              {Object.entries(analystCategories).map(([categoryKey, category]) => {
                const selectedInCategory = category.analysts.filter(analyst =>
                  selectedAnalysts.some(selected => selected.value === analyst.value)
                ).length;
                const allSelectedInCategory = selectedInCategory === category.analysts.length;

                return (
                  <Grid item xs={12} md={6} key={categoryKey}>
                    <Slide direction="up" in timeout={600}>
                      <Card sx={{
                        height: '100%',
                        background: isDarkMode ? 'rgba(255,255,255,0.05)' : '#f8f9fa',
                        border: `2px solid ${category.color}30`,
                        transition: 'all 0.3s',
                        '&:hover': {
                          transform: 'translateY(-4px)',
                          boxShadow: 4,
                          borderColor: category.color
                        }
                      }}>
                        <CardContent>
                          {/* 分类标题 */}
                          <Box sx={{ mb: 2 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Box sx={{ color: category.color }}>
                                  {category.icon}
                                </Box>
                                <Typography variant="h6" sx={{ color: category.color, fontWeight: 'bold' }}>
                                  {category.title}
                                </Typography>
                              </Box>
                              <Tooltip title={allSelectedInCategory ? '取消全选' : '全选此类'}>
                                <IconButton
                                  size="small"
                                  onClick={() => handleCategorySelectAll(categoryKey)}
                                  sx={{
                                    color: category.color,
                                    '&:hover': { bgcolor: `${category.color}20` }
                                  }}
                                >
                                  {allSelectedInCategory ? <Remove /> : <Add />}
                                </IconButton>
                              </Tooltip>
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                              {category.description}
                            </Typography>
                            <Typography variant="caption" sx={{ color: category.color, fontWeight: 'bold' }}>
                              已选择 {selectedInCategory}/{category.analysts.length} 位
                            </Typography>
                          </Box>

                          {/* 分析师列表 */}
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            {category.analysts.map((analyst, index) => {
                              const isSelected = selectedAnalysts.some(a => a.value === analyst.value);

                              return (
                                <Fade in timeout={400 + index * 100} key={analyst.value}>
                                  <Card
                                    sx={{
                                      cursor: 'pointer',
                                      transition: 'all 0.2s',
                                      bgcolor: isSelected ? `${category.color}20` : 'background.paper',
                                      border: `1px solid ${isSelected ? category.color : 'transparent'}`,
                                      '&:hover': {
                                        bgcolor: `${category.color}15`,
                                        transform: 'translateX(4px)',
                                        boxShadow: 2
                                      }
                                    }}
                                  >
                                    <CardActionArea onClick={() => handleAnalystToggle(analyst)}>
                                      <CardContent sx={{ py: 1.5 }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                          <Avatar sx={{
                                            bgcolor: isSelected ? category.color : (isDarkMode ? 'grey.600' : 'grey.300'),
                                            width: 32,
                                            height: 32,
                                            fontSize: '1rem'
                                          }}>
                                            {analyst.avatar}
                                          </Avatar>
                                          <Box sx={{ flex: 1 }}>
                                            <Typography variant="subtitle2" sx={{
                                              fontWeight: isSelected ? 'bold' : 'normal',
                                              color: isSelected ? category.color : 'text.primary'
                                            }}>
                                              {analyst.label}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary" sx={{
                                              display: '-webkit-box',
                                              WebkitLineClamp: 2,
                                              WebkitBoxOrient: 'vertical',
                                              overflow: 'hidden'
                                            }}>
                                              {analyst.description}
                                            </Typography>
                                          </Box>
                                          <Checkbox
                                            checked={isSelected}
                                            sx={{ color: category.color }}
                                          />
                                        </Box>
                                      </CardContent>
                                    </CardActionArea>
                                  </Card>
                                </Fade>
                              );
                            })}
                          </Box>
                        </CardContent>
                      </Card>
                    </Slide>
                  </Grid>
                );
              })}
            </Grid>

            {/* 已选择的分析师预览 */}
            {selectedAnalysts.length > 0 && (
              <Slide direction="up" in timeout={500}>
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    已选择的分析师
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {selectedAnalysts.map((analyst, index) => {
                      const category = Object.values(analystCategories).find(cat =>
                        cat.analysts.some(a => a.value === analyst.value)
                      );

                      return (
                        <Fade in timeout={200 + index * 50} key={analyst.value}>
                          <Chip
                            label={analyst.label}
                            onDelete={() => handleAnalystToggle(analyst)}
                            sx={{
                              background: `${category?.color}20`,
                              color: category?.color,
                              fontWeight: 'bold',
                              '& .MuiChip-deleteIcon': {
                                color: category?.color
                              }
                            }}
                          />
                        </Fade>
                      );
                    })}
                  </Box>
                </Box>
              </Slide>
            )}
          </Box>
        </Fade>
      ),
    },
  ];

  return (
    <Box>
      {/* 现代化标题区域 */}
      <Box sx={{
        background: colors.primary,
        borderRadius: 3,
        p: 4,
        mb: 4,
        color: colors.textPrimary,
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* 背景装饰元素 */}
        <Box sx={{
          position: 'absolute',
          top: -50,
          right: -50,
          width: 150,
          height: 150,
          borderRadius: '50%',
          background: colors.shimmerColor,
          animation: 'float 6s ease-in-out infinite'
        }} />

        <Box sx={{
          position: 'absolute',
          bottom: -30,
          left: -30,
          width: 100,
          height: 100,
          borderRadius: '50%',
          background: isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.1)',
          animation: 'float 4s ease-in-out infinite reverse'
        }} />

        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Typography variant="h4" component="h1" gutterBottom sx={{
            fontWeight: 'bold',
            color: colors.textPrimary,
            display: 'flex',
            alignItems: 'center',
            gap: 2
          }}>
            <Analytics sx={{
              fontSize: '3rem',
              color: colors.textPrimary,
            }} />
            价值投资大师agent
          </Typography>

          <Typography variant="h6" sx={{
            opacity: 0.9,
            fontWeight: '400',
            maxWidth: '600px',
            color: colors.textPrimary
          }}>
            汇聚全球顶级价值投资大师的智慧，为您提供专业的股票投资分析建议
          </Typography>

          <Box sx={{
            display: 'flex',
            gap: 2,
            mt: 2,
            flexWrap: 'wrap'
          }}>
            <Chip
              icon={<TrendingUp />}
              label="价值分析"
              sx={{
                background: '#fce4ec',
                color: '#c2185b',
                fontWeight: 'bold',
                border: '1px solid #f8bbd9',
                '&:hover': {
                  background: '#fce4ec',
                },
              }}
            />
            <Chip
              icon={<Person />}
              label="投资大师"
              sx={{
                background: '#fce4ec',
                color: '#c2185b',
                fontWeight: 'bold',
                border: '1px solid #f8bbd9',
                '&:hover': {
                  background: '#fce4ec',
                },
              }}
            />
            <Chip
              icon={<Analytics />}
              label="智能推荐"
              sx={{
                background: '#fce4ec',
                color: '#c2185b',
                fontWeight: 'bold',
                border: '1px solid #f8bbd9',
                '&:hover': {
                  background: '#fce4ec',
                },
              }}
            />
          </Box>
        </Box>
      </Box>

      {!isAnalyzing && activeStep < 2 ? (
        <Card sx={{
          background: colors.cardBackground,
          borderRadius: 3,
          overflow: 'hidden',
          position: 'relative',
          boxShadow: 3,
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 4,
            background: colors.primary,
          }
        }}>
          <CardContent sx={{ p: 4 }}>
            <Stepper activeStep={activeStep} orientation="vertical" sx={{
              '& .MuiStepLabel-root': {
                py: 2
              },
              '& .MuiStepIcon-root': {
                fontSize: '2rem',
                '&.Mui-active': {
                  color: colors.primary,
                  animation: 'pulse 2s infinite'
                },
                '&.Mui-completed': {
                  color: '#4caf50'
                }
              },
              '& .MuiStepContent-root': {
                borderLeft: 'none',
                ml: 2,
                pl: 2
              }
            }}>
              {steps.map((step, index) => (
                <Step key={step.label}>
                  <StepLabel>
                    <Typography variant="h6" sx={{
                      fontWeight: 'bold',
                      color: activeStep === index ? colors.primary : 'text.primary'
                    }}>
                      {step.label}
                    </Typography>
                  </StepLabel>
                  <StepContent>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {step.description}
                    </Typography>
                    {step.content}
                    <Box sx={{ mb: 2, mt: 3 }}>
                      <div>
                        <Button
                          variant="contained"
                          onClick={index === steps.length - 1 ? handleStartAnalysis : handleNext}
                          sx={{
                            mt: 1,
                            mr: 1,
                            background: colors.primary,
                            borderRadius: 2,
                            px: 3,
                            py: 1,
                            fontWeight: 'bold',
                            boxShadow: 2,
                            transition: 'all 0.3s',
                            '&:hover': {
                              transform: 'translateY(-2px)',
                              boxShadow: 4,
                              background: colors.secondary,
                            },
                            '&:disabled': {
                              background: '#ccc',
                              boxShadow: 'none',
                              transform: 'none'
                            }
                          }}
                          disabled={!isFormValid}
                        >
                          {index === steps.length - 1 ? '🚀 开始分析' : '继续 →'}
                        </Button>
                        <Button
                          disabled={index === 0}
                          onClick={handleBack}
                          sx={{
                            mt: 1,
                            mr: 1,
                            color: 'text.secondary',
                            '&:hover': {
                              bgcolor: isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)'
                            }
                          }}
                        >
                          ← 返回
                        </Button>
                      </div>
                    </Box>
                  </StepContent>
                </Step>
              ))}
            </Stepper>
          </CardContent>
        </Card>
      ) : activeStep === 2 && analysisResults ? (
        <AnalysisResults
          results={analysisResults}
          onNewAnalysis={handleReset}
        />
      ) : (
        <AnalysisProgress
          progress={progress}
          tickers={tickers.split(',').map(t => t.trim())}
          analysts={selectedAnalysts}
          error={analysisError}
          onCancel={handleReset}
        />
      )}

      {analysisError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {analysisError}
        </Alert>
      )}
    </Box>
  );
}

function AnalysisProgress({ progress, tickers, analysts, error, onCancel }) {
  const [elapsedTime, setElapsedTime] = useState(0);

  // Track elapsed time
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Format time as mm:ss
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate overall progress percentage
  const calculateOverallProgress = () => {
    let totalItems = tickers.length * analysts.length;
    let completedPercentage = 0;

    tickers.forEach(ticker => {
      analysts.forEach(analyst => {
        const pct = progress[analyst.value]?.[ticker]?.percent || 0;
        completedPercentage += pct;
      });
    });

    return Math.round(completedPercentage / totalItems);
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              分析进行中
            </Typography>
            <Typography variant="body2" color="text.secondary">
              已用时间：{formatTime(elapsedTime)} | 总体进度：{calculateOverallProgress()}%
            </Typography>
          </Box>
          <Button
            variant="outlined"
            color="error"
            size="small"
            onClick={onCancel}
          >
            取消
          </Button>
        </Box>

        <LinearProgress
          variant="determinate"
          value={calculateOverallProgress()}
          sx={{ mb: 3, height: 10, borderRadius: 5 }}
        />

        {error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : (
          <Box>
            {tickers.map(ticker => (
              <Box key={ticker} sx={{ mb: 4 }}>
                <Typography variant="subtitle1" sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                  <Box component="span" sx={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    bgcolor: 'primary.main',
                    display: 'inline-block',
                    mr: 1
                  }} />
                  {ticker}
                </Typography>
                <Grid container spacing={2}>
                  {analysts.map(analyst => {
                    const agentProgress = progress[analyst.value]?.[ticker];
                    const pct = agentProgress ? agentProgress.percent : 0;
                    const status = agentProgress ? agentProgress.status : '等待中...';

                    // Determine color based on progress
                    let statusColor = '#666'; // default gray
                    if (pct === 100) statusColor = '#4caf50'; // green
                    else if (pct > 70) statusColor = '#2196f3'; // blue
                    else if (pct > 30) statusColor = '#ff9800'; // orange
                    else if (pct > 0) statusColor = '#f44336'; // red

                    return (
                      <Grid item xs={12} md={6} key={analyst.value}>
                        <Card variant="outlined" sx={{
                          mb: 1,
                          borderColor: pct === 100 ? 'success.main' : 'divider',
                          transition: 'all 0.3s',
                          transform: pct === 100 ? 'translateY(-2px)' : 'none',
                          boxShadow: pct === 100 ? 2 : 0
                        }}>
                          <CardContent sx={{ pb: '16px !important' }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                              <Typography variant="subtitle2">
                                {analyst.label}
                              </Typography>
                              <Typography variant="body2" sx={{ color: statusColor, fontWeight: 'bold' }}>
                                {pct}%
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={pct}
                              sx={{
                                mb: 1,
                                height: 6,
                                borderRadius: 1,
                                '.MuiLinearProgress-bar': {
                                  backgroundColor: statusColor
                                }
                              }}
                            />
                            <Typography variant="caption" sx={{ color: statusColor }}>
                              {status}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    );
                  })}
                </Grid>
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

function AnalysisResults({ results, onNewAnalysis }) {
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table' or 'raw'
  const [filterSignal, setFilterSignal] = useState('all'); // 'all', 'buy', 'sell', 'neutral'
  const [sortBy, setSortBy] = useState('confidence'); // 'confidence', 'signal', 'analyst'
  const [expandedCards, setExpandedCards] = useState(new Set());

  // 将分析师代码映射为中文显示名称
  const getAnalystDisplayName = (agentName) => {
    const analystMapping = {
      'warren_buffett_agent': '巴菲特',
      'charlie_munger_agent': '芒格',
      'ben_graham_agent': '格雷厄姆',
      'bill_ackman_agent': '艾克曼',
      'cathie_wood_agent': '木头姐',
      'peter_lynch_agent': '彼得·林奇',
      'phil_fisher_agent': '菲尔·费舍尔'
    };
    return analystMapping[agentName] || agentName;
  };

  // 解析结果数据
  const parseResults = () => {
    if (!results || !results.ticker_analyses) return [];

    const parsed = [];
    Object.entries(results.ticker_analyses).forEach(([ticker, analyses]) => {
      if (Array.isArray(analyses)) {
        analyses.forEach(analysis => {
          parsed.push({
            ticker,
            analyst: getAnalystDisplayName(analysis.agent_name),
            signal: analysis.signal,
            confidence: analysis.confidence,
            reasoning: analysis.reasoning
          });
        });
      }
    });

    return parsed;
  };

  const analysisData = parseResults();

  // 获取信号颜色和图标
  const getSignalInfo = (signal) => {
    const normalizedSignal = signal?.toLowerCase() || '';
    if (normalizedSignal.includes('买入') || normalizedSignal.includes('buy')) {
      return {
        color: '#c2185b',
        icon: '📈',
        text: '买入',
        bgColorLight: '#fce4ec',
        bgColorDark: '#fce4ec'
      };
    } else if (normalizedSignal.includes('卖出') || normalizedSignal.includes('sell')) {
      return {
        color: '#c2185b',
        icon: '📉',
        text: '卖出',
        bgColorLight: '#fce4ec',
        bgColorDark: '#fce4ec'
      };
    } else {
      return {
        color: '#c2185b',
        icon: '➖',
        text: '中性',
        bgColorLight: '#fce4ec',
        bgColorDark: '#fce4ec'
      };
    }
  };

  // 筛选和排序数据
  const filteredData = analysisData.filter(item => {
    if (filterSignal === 'all') return true;
    const signalInfo = getSignalInfo(item.signal);
    return signalInfo.text.includes(filterSignal === 'buy' ? '买入' : filterSignal === 'sell' ? '卖出' : '中性');
  });

  const sortedData = [...filteredData].sort((a, b) => {
    if (sortBy === 'confidence') return b.confidence - a.confidence;
    if (sortBy === 'signal') return a.signal.localeCompare(b.signal);
    if (sortBy === 'analyst') return a.analyst.localeCompare(b.analyst);
    return 0;
  });

  // 统计信息
  const stats = {
    total: analysisData.length,
    buy: analysisData.filter(item => getSignalInfo(item.signal).text.includes('买入')).length,
    sell: analysisData.filter(item => getSignalInfo(item.signal).text.includes('卖出')).length,
    neutral: analysisData.filter(item => getSignalInfo(item.signal).text.includes('中性')).length,
    avgConfidence: Math.round(analysisData.reduce((sum, item) => sum + item.confidence, 0) / analysisData.length || 0)
  };

  const toggleCardExpansion = (index) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedCards(newExpanded);
  };

  return (
    <Box>
      {/* 头部控制区 */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h6">
          股票分析结果 ({new Date().toISOString().split('T')[0]})
        </Typography>
        <Button
          variant="outlined"
          onClick={onNewAnalysis}
        >
          重新分析
        </Button>
      </Box>

      {/* 统计概览 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <Card sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="primary">{stats.total}</Typography>
            <Typography variant="body2">总分析数</Typography>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card sx={{
            p: 2,
            textAlign: 'center',
            bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(76, 175, 80, 0.1)' : '#e8f5e9',
            border: (theme) => theme.palette.mode === 'dark' ? '1px solid rgba(76, 175, 80, 0.3)' : 'none'
          }}>
            <Typography variant="h6" sx={{ color: '#4caf50' }}>📈 {stats.buy}</Typography>
            <Typography variant="body2">买入信号</Typography>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card sx={{
            p: 2,
            textAlign: 'center',
            bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(244, 67, 54, 0.1)' : '#ffebee',
            border: (theme) => theme.palette.mode === 'dark' ? '1px solid rgba(244, 67, 54, 0.3)' : 'none'
          }}>
            <Typography variant="h6" sx={{ color: '#f44336' }}>📉 {stats.sell}</Typography>
            <Typography variant="body2">卖出信号</Typography>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="primary">{stats.avgConfidence}%</Typography>
            <Typography variant="body2">平均置信度</Typography>
          </Card>
        </Grid>
      </Grid>

      {/* 控制选项 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" gutterBottom>显示模式</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  size="small"
                  variant={viewMode === 'cards' ? 'contained' : 'outlined'}
                  onClick={() => setViewMode('cards')}
                >
                  卡片
                </Button>
                <Button
                  size="small"
                  variant={viewMode === 'table' ? 'contained' : 'outlined'}
                  onClick={() => setViewMode('table')}
                >
                  表格
                </Button>
                <Button
                  size="small"
                  variant={viewMode === 'raw' ? 'contained' : 'outlined'}
                  onClick={() => setViewMode('raw')}
                >
                  原始数据
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" gutterBottom>筛选信号</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Chip
                  label="全部"
                  onClick={() => setFilterSignal('all')}
                  color={filterSignal === 'all' ? 'primary' : 'default'}
                  size="small"
                  sx={{
                    background: filterSignal === 'all' ? '#fce4ec' : 'transparent',
                    color: filterSignal === 'all' ? '#c2185b' : 'text.secondary',
                    border: filterSignal === 'all' ? '1px solid #f8bbd9' : '1px solid #e0e0e0',
                    '&:hover': {
                      background: '#fce4ec',
                      color: '#c2185b'
                    }
                  }}
                />
                <Chip
                  label="买入"
                  onClick={() => setFilterSignal('buy')}
                  color={filterSignal === 'buy' ? 'success' : 'default'}
                  size="small"
                  sx={{
                    background: filterSignal === 'buy' ? '#e8f5e9' : 'transparent',
                    color: filterSignal === 'buy' ? '#4caf50' : 'text.secondary',
                    border: filterSignal === 'buy' ? '1px solid #c8e6c9' : '1px solid #e0e0e0',
                    '&:hover': {
                      background: '#e8f5e9',
                      color: '#4caf50'
                    }
                  }}
                />
                <Chip
                  label="卖出"
                  onClick={() => setFilterSignal('sell')}
                  color={filterSignal === 'sell' ? 'error' : 'default'}
                  size="small"
                  sx={{
                    background: filterSignal === 'sell' ? '#ffebee' : 'transparent',
                    color: filterSignal === 'sell' ? '#f44336' : 'text.secondary',
                    border: filterSignal === 'sell' ? '1px solid #ffcdd2' : '1px solid #e0e0e0',
                    '&:hover': {
                      background: '#ffebee',
                      color: '#f44336'
                    }
                  }}
                />
                <Chip
                  label="中性"
                  onClick={() => setFilterSignal('neutral')}
                  color={filterSignal === 'neutral' ? 'warning' : 'default'}
                  size="small"
                  sx={{
                    background: filterSignal === 'neutral' ? '#fff3e0' : 'transparent',
                    color: filterSignal === 'neutral' ? '#ff9800' : 'text.secondary',
                    border: filterSignal === 'neutral' ? '1px solid #ffcc02' : '1px solid #e0e0e0',
                    '&:hover': {
                      background: '#fff3e0',
                      color: '#ff9800'
                    }
                  }}
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" gutterBottom>排序方式</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Chip
                  label="置信度"
                  onClick={() => setSortBy('confidence')}
                  color={sortBy === 'confidence' ? 'primary' : 'default'}
                  size="small"
                  sx={{
                    background: sortBy === 'confidence' ? '#fce4ec' : 'transparent',
                    color: sortBy === 'confidence' ? '#c2185b' : 'text.secondary',
                    border: sortBy === 'confidence' ? '1px solid #f8bbd9' : '1px solid #e0e0e0',
                    '&:hover': {
                      background: '#fce4ec',
                      color: '#c2185b'
                    }
                  }}
                />
                <Chip
                  label="信号"
                  onClick={() => setSortBy('signal')}
                  color={sortBy === 'signal' ? 'primary' : 'default'}
                  size="small"
                  sx={{
                    background: sortBy === 'signal' ? '#fce4ec' : 'transparent',
                    color: sortBy === 'signal' ? '#c2185b' : 'text.secondary',
                    border: sortBy === 'signal' ? '1px solid #f8bbd9' : '1px solid #e0e0e0',
                    '&:hover': {
                      background: '#fce4ec',
                      color: '#c2185b'
                    }
                  }}
                />
                <Chip
                  label="分析师"
                  onClick={() => setSortBy('analyst')}
                  color={sortBy === 'analyst' ? 'primary' : 'default'}
                  size="small"
                  sx={{
                    background: sortBy === 'analyst' ? '#fce4ec' : 'transparent',
                    color: sortBy === 'analyst' ? '#c2185b' : 'text.secondary',
                    border: sortBy === 'analyst' ? '1px solid #f8bbd9' : '1px solid #e0e0e0',
                    '&:hover': {
                      background: '#fce4ec',
                      color: '#c2185b'
                    }
                  }}
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" gutterBottom>数据统计</Typography>
              <Typography variant="body2" color="text.secondary">
                显示 {sortedData.length} / {analysisData.length} 条结果
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 内容展示区 */}
      {viewMode === 'cards' && (
        <Grid container spacing={1}>
          {sortedData.map((item, index) => {
            const signalInfo = getSignalInfo(item.signal);
            const isExpanded = expandedCards.has(index);

            return (
              <Grid item xs={12} md={6} lg={4} key={index}>
                <Card
                  sx={{
                    borderLeft: `4px solid ${signalInfo.color}`,
                    transition: 'all 0.2s',
                    '&:hover': {
                      boxShadow: 3,
                      transform: 'translateY(-2px)'
                    }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {item.ticker}
                        <Chip
                          icon={<span>{signalInfo.icon}</span>}
                          label={signalInfo.text}
                          size="small"
                          sx={{
                            background: (theme) => theme.palette.mode === 'dark' ? signalInfo.bgColorDark : signalInfo.bgColorLight,
                            color: signalInfo.color,
                            fontWeight: 'bold'
                          }}
                        />
                      </Typography>
                      <Typography variant="h6" sx={{ color: signalInfo.color, fontWeight: 'bold' }}>
                        {item.confidence}%
                      </Typography>
                    </Box>

                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      分析师：{item.analyst}
                    </Typography>

                    {/* 置信度进度条 */}
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="caption">置信度</Typography>
                        <Typography variant="caption">{item.confidence}%</Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={item.confidence}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          '.MuiLinearProgress-bar': {
                            backgroundColor: signalInfo.color
                          }
                        }}
                      />
                    </Box>

                    {/* 分析理由 */}
                    <Box>
                      <Typography variant="body2" sx={{
                        display: '-webkit-box',
                        WebkitLineClamp: isExpanded ? 'none' : 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        mb: 1
                      }}>
                        {item.reasoning}
                      </Typography>
                      <Button
                        size="small"
                        onClick={() => toggleCardExpansion(index)}
                        sx={{ p: 0, minWidth: 'auto' }}
                      >
                        {isExpanded ? '收起' : '展开'}
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {viewMode === 'table' && (
        <Card>
          <CardContent>
            <Box sx={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                    <th style={{ padding: '12px', textAlign: 'left' }}>股票</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>分析师</th>
                    <th style={{ padding: '12px', textAlign: 'center' }}>信号</th>
                    <th style={{ padding: '12px', textAlign: 'center' }}>置信度</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>分析理由</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedData.map((item, index) => {
                    const signalInfo = getSignalInfo(item.signal);
                    return (
                      <tr key={index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={{ padding: '12px', fontWeight: 'bold' }}>{item.ticker}</td>
                        <td style={{ padding: '12px' }}>{item.analyst}</td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <Chip
                            icon={<span>{signalInfo.icon}</span>}
                            label={signalInfo.text}
                            size="small"
                            sx={{
                              background: (theme) => theme.palette.mode === 'dark' ? signalInfo.bgColorDark : signalInfo.bgColorLight,
                              color: signalInfo.color,
                              fontWeight: 'bold'
                            }}
                          />
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={item.confidence}
                              sx={{
                                width: 60,
                                height: 6,
                                borderRadius: 3,
                                '.MuiLinearProgress-bar': {
                                  backgroundColor: signalInfo.color
                                }
                              }}
                            />
                            <Typography variant="body2" sx={{ color: signalInfo.color, fontWeight: 'bold' }}>
                              {item.confidence}%
                            </Typography>
                          </Box>
                        </td>
                        <td style={{ padding: '12px', maxWidth: '300px' }}>
                          <Typography variant="body2" sx={{
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden'
                          }}>
                            {item.reasoning}
                          </Typography>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Box>
          </CardContent>
        </Card>
      )}

      {viewMode === 'raw' && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              原始数据 (JSON 格式)
            </Typography>
            <Box sx={{
              backgroundColor: (theme) => theme.palette.mode === 'dark' ? '#1e1e1e' : '#f5f5f5',
              p: 2,
              borderRadius: 1,
              maxHeight: '600px',
              overflowY: 'auto',
              fontFamily: 'monospace'
            }}>
              <pre style={{
                margin: 0,
                whiteSpace: 'pre-wrap',
                fontSize: '0.875rem',
                lineHeight: 1.4,
                color: isDarkMode ? '#fff' : 'inherit'
              }}>
                {JSON.stringify(results, null, 2)}
              </pre>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

const isValidDate = (dateString) => {
  // Basic date validation for YYYY-MM-DD format
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(dateString)) return false;

  const date = new Date(dateString);
  return !isNaN(date.getTime());
}; 