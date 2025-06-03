import { Box, Typography, Card, CardContent, Container, Chip } from '@mui/material';
import { Construction, Schedule, Code } from '@mui/icons-material';

export default function Backtest() {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center'
      }}>
        <Card sx={{
          maxWidth: 500,
          p: 4,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          boxShadow: 3,
          borderRadius: 3
        }}>
          <CardContent>
            <Construction sx={{ fontSize: 80, mb: 2, opacity: 0.9 }} />
            
            <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
              回测功能
            </Typography>
            
            <Typography variant="h6" sx={{ mb: 3, opacity: 0.9 }}>
              开发中，请敬请期待
            </Typography>
            
            <Typography variant="body1" sx={{ mb: 3, opacity: 0.8 }}>
              我们正在努力开发强大的回测功能，让您能够验证投资策略的历史表现。
            </Typography>
            
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                icon={<Schedule />}
                label="即将发布"
                sx={{ 
                  background: 'rgba(255,255,255,0.2)', 
                  color: 'white',
                  fontWeight: 'bold'
                }}
              />
              <Chip
                icon={<Code />}
                label="功能开发中"
                sx={{ 
                  background: 'rgba(255,255,255,0.2)', 
                  color: 'white',
                  fontWeight: 'bold'
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
} 