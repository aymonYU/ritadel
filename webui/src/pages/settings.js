import { useState } from 'react';
import { Box, Typography, Card, CardContent, TextField, Button, Grid, Switch, FormControlLabel, Divider, Select, MenuItem, FormControl, InputLabel, Alert, Snackbar } from '@mui/material';
import { Save as SaveIcon, Refresh as RefreshIcon } from '@mui/icons-material';

export default function Settings() {
  // 状态变量：OpenAI API 密钥
  // State variable: OpenAI API Key
  const [openAIKey, setOpenAIKey] = useState('');
  // Anthropic, Groq, 和 Gemini API 密钥状态变量已被移除，因为模型固定为 GPT-4o
  // Anthropic, Groq, and Gemini API key state variables have been removed as the model is fixed to GPT-4o
  // const [anthropicKey, setAnthropicKey] = useState('');
  // const [groqKey, setGroqKey] = useState('');
  // const [geminiKey, setGeminiKey] = useState('');
  // defaultModel 状态变量已被移除，因为模型固定为 GPT-4o
  // defaultModel state variable has been removed as the model is fixed to GPT-4o
  // const [defaultModel, setDefaultModel] = useState('gpt-4o'); 
  const [saveHistory, setSaveHistory] = useState(true);
  const [backtestDefaults, setBacktestDefaults] = useState({
    initialCapital: 100000,
    marginRequirement: 0.5
  });
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  
  const handleSaveSettings = () => {
    setSnackbarMessage('Settings saved successfully');
    setOpenSnackbar(true);
  };
  
  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
  };
  
  const handleReset = () => {
    setOpenAIKey('');
    // Anthropic, Groq, 和 Gemini API 密钥的重置逻辑已被移除
    // Reset logic for Anthropic, Groq, and Gemini API keys has been removed
    // setAnthropicKey('');
    // setGroqKey('');
    // setGeminiKey('');
    // defaultModel 的重置逻辑已被移除
    // Reset logic for defaultModel has been removed
    // setDefaultModel('gpt-4o');
    setSaveHistory(true);
    setBacktestDefaults({
      initialCapital: 100000,
      marginRequirement: 0.5
    });
    
    setSnackbarMessage('Settings reset to defaults');
    setOpenSnackbar(true);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                API Keys
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <TextField
                  label="OpenAI API Key"
                  fullWidth
                  margin="normal"
                  type="password"
                  value={openAIKey}
                  onChange={(e) => setOpenAIKey(e.target.value)}
                  placeholder="sk-..."
                />
                {/* Anthropic API 密钥输入框已被移除 */}
                {/* Anthropic API Key input field has been removed */}
                {/*
                <TextField
                  label="Anthropic API Key"
                  fullWidth
                  margin="normal"
                  type="password"
                  value={anthropicKey}
                  onChange={(e) => setAnthropicKey(e.target.value)}
                  placeholder="sk-ant-..."
                />
                */}
                {/* Groq API 密钥输入框已被移除 */}
                {/* Groq API Key input field has been removed */}
                {/*
                <TextField
                  label="Groq API Key"
                  fullWidth
                  margin="normal"
                  type="password"
                  value={groqKey}
                  onChange={(e) => setGroqKey(e.target.value)}
                  placeholder="gsk_..."
                />
                */}
                {/* Gemini API 密钥输入框已被移除 */}
                {/* Gemini API Key input field has been removed */}
                {/*
                <TextField
                  label="Gemini API Key"
                  fullWidth
                  margin="normal"
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="..."
                />
                */}
              </Box>
              
              <Typography variant="h6" gutterBottom>
                LLM Model {/* LLM 模型 */}
              </Typography>
              {/* 模型选择下拉框已被移除，替换为固定模型信息的文本显示 */}
              {/* Model selection dropdown has been removed and replaced with text displaying fixed model information. */}
              <Typography variant="body1" sx={{ mt: 1, mb: 2 }}>
                系统当前固定使用 OpenAI GPT-4o 模型。
                <br />
                (The system currently uses a fixed OpenAI GPT-4o model.)
              </Typography>
              {/*
              <FormControl fullWidth margin="normal">
                <InputLabel>Default LLM Model</InputLabel>
                <Select
                  value={defaultModel}
                  label="Default LLM Model"
                  onChange={(e) => setDefaultModel(e.target.value)}
                >
                  <MenuItem value="gpt-4o">[openai] gpt-4o</MenuItem>
                  <MenuItem value="gpt-4o-mini">[openai] gpt-4o-mini</MenuItem>
                  <MenuItem value="claude-3-5-sonnet-latest">[anthropic] claude-3.5-sonnet</MenuItem>
                  <MenuItem value="claude-3-7-sonnet-latest">[anthropic] claude-3.7-sonnet</MenuItem>
                  <MenuItem value="deepseek-r1-distill-llama-70b">[groq] deepseek-r1 70b</MenuItem>
                  <MenuItem value="llama-3.3-70b-versatile">[groq] llama-3.3 70b</MenuItem>
                  <MenuItem value="gemini-2.0-flash">[gemini] gemini-2.0-flash</MenuItem>
                </Select>
              </FormControl>
              */}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Application Settings
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch 
                    checked={saveHistory}
                    onChange={(e) => setSaveHistory(e.target.checked)}
                  />
                }
                label="Save analysis history"
              />
              
              <Divider sx={{ my: 3 }} />
              
              <Typography variant="h6" gutterBottom>
                Backtest Defaults
              </Typography>
              
              <TextField
                label="Initial Capital"
                fullWidth
                margin="normal"
                type="number"
                value={backtestDefaults.initialCapital}
                onChange={(e) => setBacktestDefaults({...backtestDefaults, initialCapital: Number(e.target.value)})}
                InputProps={{
                  startAdornment: '$',
                }}
              />
              
              <TextField
                label="Default Margin Requirement"
                fullWidth
                margin="normal"
                type="number"
                value={backtestDefaults.marginRequirement}
                onChange={(e) => setBacktestDefaults({...backtestDefaults, marginRequirement: Number(e.target.value)})}
                inputProps={{
                  min: 0,
                  max: 1,
                  step: 0.1,
                }}
                helperText="A value of 0.5 means 50% margin is required for short positions"
              />
              
              <Alert severity="info" sx={{ mt: 3 }}>
                These settings are used as defaults for new backtest runs. You can override them when setting up individual backtests.
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleReset}
        >
          Reset to Defaults
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSaveSettings}
        >
          Save Settings
        </Button>
      </Box>
      
      <Snackbar
        open={openSnackbar}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        message={snackbarMessage}
      />
    </Box>
  );
} 