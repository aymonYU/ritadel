import { useState, useEffect } from 'react';
import { Box, Grid, Typography, Card, CardContent, TextField, Button, Autocomplete, Checkbox, Chip, FormControlLabel, FormGroup, Divider, Stepper, Step, StepLabel, StepContent, Paper, LinearProgress, Alert } from '@mui/material';
import { Search as SearchIcon, Send as SendIcon, Check as CheckIcon } from '@mui/icons-material';
import { runAnalysis } from '../utils/api';

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

const analystOptions = [
  { label: 'Warren Buffett (巴菲特)', value: 'warren_buffett_agent', description: '分析具有强大基本面和合理价格的优质企业' },
  { label: 'Charlie Munger (芒格)', value: 'charlie_munger_agent', description: '使用心理模型评估公司，并考虑护城河和管理质量' },
  { label: 'Ben Graham (格雷厄姆)', value: 'ben_graham_agent', description: '专注于深度价值股票，交易价格低于内在价值，具有安全边际' },
  { label: 'Bill Ackman (艾克曼)', value: 'bill_ackman_agent', description: '识别具有长期增长和激进潜力的优质企业' },
  { label: 'Cathie Wood (木头姐)', value: 'cathie_wood_agent', description: '专注于颠覆性创新和高速增长的技术公司' },
  { label: 'Peter Lynch (彼得·林奇)', value: 'peter_lynch_agent', description: '专注于具有强大基本面和增长潜力的公司' },
  { label: 'Phil Fisher (菲尔·费舍尔)', value: 'phil_fisher_agent', description: '识别具有强大竞争优势和增长潜力的公司' },

  
  // { label: 'WSB', value: 'wsb_agent', description: 'Identifies meme stocks, short squeeze candidates, and momentum plays' },
  // { label: 'Technical Analysis', value: 'technical_analyst_agent', description: 'Uses price patterns, trends, and indicators to generate trading signals' },
  // { label: 'Fundamental Analysis', value: 'fundamentals_agent', description: 'Examines company fundamentals like profitability, growth, and financial health' },
  // { label: 'Sentiment Analysis', value: 'sentiment_agent', description: 'Analyzes market sentiment from news and insider trading' },
  // { label: 'Valuation Analysis', value: 'valuation_agent', description: 'Calculates intrinsic value using multiple valuation methodologies' },
  // { label: 'Risk Management', value: 'risk_management_agent', description: 'Controls position sizing based on portfolio risk factors' },
];

export default function Analysis() {
  const [activeStep, setActiveStep] = useState(0);
  const [tickers, setTickers] = useState('');
  const [selectedAnalysts, setSelectedAnalysts] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [progress, setProgress] = useState({});
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isFormValid, setIsFormValid] = useState(false);

  useEffect(() => {
    let valid = false;
    
    // Step-specific validation
    switch (activeStep) {
      case 0: // Select Stocks step
        // For the first step, only ticker is required
        valid = tickers.trim() !== '';
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
    
    // For first step, just check ticker input
    if (activeStep === 0) {
      if (!tickers.trim()) {
        setAnalysisError("请输入至少一个股票代码");
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
      description: '输入股票代码，用逗号分隔',
      content: (
        <Box sx={{ mt: 2 }}>
          <TextField
            label="股票代码"
            fullWidth
            margin="normal"
            placeholder="AAPL, MSFT, GOOGL"
            value={tickers}
            onChange={(e) => setTickers(e.target.value)}
            helperText="输入股票代码，用逗号分隔"
          />
        </Box>
      ),
    },
    {
      label: '选择分析师',
      description: '选择AI分析师来评估你的股票',
      content: (
        <Box sx={{ mt: 2 }}>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle2">
              选择AI分析师来评估你的股票
            </Typography>
            <Button 
              size="small" 
              onClick={handleSelectAllAnalysts}
              variant="outlined"
            >
              {selectedAnalysts.length === analystOptions.length ? '取消选择所有' : '选择所有'}
            </Button>
          </Box>
          
          <Grid container spacing={2}>
            {analystOptions.map((analyst) => (
              <Grid item xs={12} md={6} key={analyst.value}>
                <Box 
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    p: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                    opacity: selectedAnalysts.some(a => a.value === analyst.value) ? 1 : 0.7,
                    transition: 'all 0.2s',
                    '&:hover': {
                      borderColor: 'primary.main',
                      boxShadow: 1,
                      opacity: 1,
                    },
                    cursor: 'pointer',
                  }}
                  onClick={() => {
                    if (selectedAnalysts.some(a => a.value === analyst.value)) {
                      setSelectedAnalysts(selectedAnalysts.filter(a => a.value !== analyst.value));
                    } else {
                      setSelectedAnalysts([...selectedAnalysts, analyst]);
                    }
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2">
                      {analyst.label}
                    </Typography>
                    <Checkbox 
                      checked={selectedAnalysts.some(a => a.value === analyst.value)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedAnalysts([...selectedAnalysts, analyst]);
                        } else {
                          setSelectedAnalysts(selectedAnalysts.filter(a => a.value !== analyst.value));
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {analyst.description}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        股票分析
      </Typography>
      
      {!isAnalyzing && activeStep < 2 ? (
        <Card>
          <CardContent>
            <Stepper activeStep={activeStep} orientation="vertical">
              {steps.map((step, index) => (
                <Step key={step.label}>
                  <StepLabel>
                    <Typography variant="subtitle1">{step.label}</Typography>
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
                          sx={{ mt: 1, mr: 1 }}
                          disabled={!isFormValid}
                        >
                          {index === steps.length - 1 ? '开始分析' : '继续'}
                        </Button>
                        <Button
                          disabled={index === 0}
                          onClick={handleBack}
                          sx={{ mt: 1, mr: 1 }}
                        >
                          返回
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
                  }}/>
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
  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
      
      {/* 原始数据 */}
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
              color: (theme) => theme.palette.mode === 'dark' ? '#fff' : 'inherit'
            }}>
              {JSON.stringify(results, null, 2)}
            </pre>
          </Box>
        </CardContent>
      </Card>
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