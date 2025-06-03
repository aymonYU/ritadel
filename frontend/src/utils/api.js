import axios from 'axios';

// 根据环境动态配置 API URL
const getApiUrl = () => {
  if (process.env.NODE_ENV === 'development') {
    // 开发环境使用环境变量或本地后端
    return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000'
  }
  // 生产环境直接使用云函数URL
  return 'https://ai-backend-165763-6-1258111923.sh.run.tcloudbase.com';
};

const API_URL = getApiUrl();

// 在开发环境中打印 API URL 以便调试
if (process.env.NODE_ENV === 'development') {
  console.log('API URL:', API_URL);
} else {
  console.error('Production API URL:', API_URL);
}

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API functions
export const getModels = async () => {
  try {
    const response = await api.get('/api/models');
    return response.data;
  } catch (error) {
    console.error('Error fetching models:', error);
    throw error;
  }
};

export const getAnalysts = async () => {
  try {
    const response = await api.get('/api/analysts');
    return response.data;
  } catch (error) {
    console.error('Error fetching analysts:', error);
    throw error;
  }
};

export const runAnalysis = async (params) => {
  try {
    const response = await api.post('/api/analysis', params);
    
    // Process the results to ensure signal consistency 
    if (response.data && response.data.ticker_analyses) {
      // For each ticker, ensure the overall signal matches the strongest analyst signal
      Object.keys(response.data.ticker_analyses).forEach(ticker => {
        const analysis = response.data.ticker_analyses[ticker];
        
        // If there's only one analyst, use their signal directly
        if (analysis.signals && Object.keys(analysis.signals).length === 1) {
          const analystSignal = Object.values(analysis.signals)[0];
          // Ensure the overall signal is set to match the analyst's signal
          analysis.signals.overall = analystSignal;
        }
      });
    }
    
    return response.data;
  } catch (error) {
    console.error('Error running analysis:', error);
    throw error;
  }
};

export const runBacktest = async (params) => {
  try {
    const response = await api.post('/api/backtest', params);
    return response.data;
  } catch (error) {
    console.error('Error running backtest:', error);
    throw error;
  }
};

export const runRoundTable = async (params) => {
  try {
    const response = await api.post('/api/round-table', params);
    return response.data;
  } catch (error) {
    console.error('Error running round table:', error);
    throw error;
  }
};

export const getEnvConfig = async () => {
  try {
    const response = await api.get('/api/env');
    return response.data;
  } catch (error) {
    console.error('Error fetching environment configuration:', error);
    throw error;
  }
};

export default api; 