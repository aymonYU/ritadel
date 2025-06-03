import { Box, Typography, Card, CardContent, Container, Chip } from '@mui/material';
import { Construction, Schedule, Code } from '@mui/icons-material';

export default function Settings() {
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
          background: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
          color: '#8b4513',
          boxShadow: 3,
          borderRadius: 3
        }}>
          <CardContent>
            <Construction sx={{ fontSize: 80, mb: 2, opacity: 0.9 }} />
            
            <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
              设置功能
            </Typography>
            
            <Typography variant="h6" sx={{ mb: 3, opacity: 0.9 }}>
              开发中，请敬请期待
            </Typography>
            
            <Typography variant="body1" sx={{ mb: 3, opacity: 0.8 }}>
              我们正在开发完整的设置功能，让您能够自定义应用的各种配置选项。
            </Typography>
            
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                icon={<Schedule />}
                label="即将发布"
                sx={{ 
                  background: 'rgba(139, 69, 19, 0.2)', 
                  color: '#8b4513',
                  fontWeight: 'bold'
                }}
              />
              <Chip
                icon={<Code />}
                label="功能开发中"
                sx={{ 
                  background: 'rgba(139, 69, 19, 0.2)', 
                  color: '#8b4513',
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