import axios from 'axios';

// 根据环境动态配置 API URL
const getApiUrl = () => {
  // 优先级：环境变量 > 生产环境检测 > 默认开发环境
  if (typeof window !== 'undefined') {
    // 客户端环境
    const env = process.env.NODE_ENV;
    const customApiUrl = process.env.NEXT_PUBLIC_API_URL;
    
    if (customApiUrl) {
      return customApiUrl;
    }
    
    // 生产环境检测
    if (env === 'production') {
      const { protocol, hostname, port } = window.location;
      // 生产环境中，假设API服务与前端在同一域名下的不同端口
      const apiPort = process.env.NEXT_PUBLIC_API_PORT || '5000';
      return `${protocol}//${hostname}:${apiPort}`;
    }
    
    // 开发环境默认值
    return process.env.NEXT_PUBLIC_DEV_API_URL || 'http://127.0.0.1:5000';
  }
  
  // 服务端渲染环境
  return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';
};

const API_URL = getApiUrl();

// 在开发环境中打印 API URL 以便调试
if (process.env.NODE_ENV === 'development') {
  console.log('API URL:', API_URL);
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