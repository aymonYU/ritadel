import { useState, useEffect } from 'react';
import { Box, Paper, Typography, IconButton } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

export default function SimpleConsole() {
  const [messages, setMessages] = useState(['Console initialized']);
  const [connected, setConnected] = useState(false);
  
  useEffect(() => {
    // Add this to check if the component is rendered
    console.log('SimpleConsole mounted');
    setMessages(prev => [...prev, 'Attempting WebSocket connection...']);
    
    let ws = null;
    try {
      ws = new WebSocket(`ws://127.0.0.1:5000/ws/logs`);
      
      ws.onopen = () => {
        setConnected(true);
        setMessages(prev => [...prev, 'WebSocket connected']);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setMessages(prev => [...prev, data.message]);
        } catch (e) {
          setMessages(prev => [...prev, `Error parsing: ${event.data}`]);
        }
      };
      
      ws.onerror = () => {
        setMessages(prev => [...prev, 'WebSocket error']);
      };
      
      ws.onclose = () => {
        setConnected(false);
        setMessages(prev => [...prev, 'WebSocket closed']);
      };
    } catch (error) {
      setMessages(prev => [...prev, `WebSocket setup error: ${error.message}`]);
    }
    
    return () => {
      if (ws) ws.close();
    };
  }, []);
  
  return (
    <Paper 
      elevation={3}
      sx={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        width: 400,
        height: 300,
        zIndex: 9999,
        overflow: 'auto',
        backgroundColor: '#000',
        color: '#0f0',
        border: '3px solid red', // Very visible border
        fontFamily: 'monospace',
        padding: 1
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="subtitle2" sx={{ color: '#fff' }}>
          Console {connected ? '(Connected)' : '(Disconnected)'}
        </Typography>
        <IconButton size="small" sx={{ color: '#fff' }} onClick={() => setMessages([])}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>
      
      <Box sx={{ height: 'calc(100% - 30px)', overflowY: 'auto' }}>
        {messages.map((msg, i) => (
          <Typography key={i} variant="body2" sx={{ fontSize: '0.8rem' }}>
            {msg}
          </Typography>
        ))}
      </Box>
    </Paper>
  );
} 