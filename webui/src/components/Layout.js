import { useState } from 'react';
import { Box, AppBar, Toolbar, Typography, Drawer, IconButton, List, ListItem, ListItemIcon, ListItemText, Divider, useMediaQuery, Avatar } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { Menu as MenuIcon, Dashboard as DashboardIcon, ShowChart as ChartIcon, Assessment as AssessmentIcon, Settings as SettingsIcon, History as HistoryIcon, People as PeopleIcon } from '@mui/icons-material';
import Link from 'next/link';
import { useRouter } from 'next/router';

// 添加CSS动画样式
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = `
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

    @keyframes pulse-glow {
      0%, 100% {
        box-shadow: 0 0 10px rgba(255,255,255,0.5);
        transform: scale(1);
      }
      50% {
        box-shadow: 0 0 15px rgba(255,255,255,0.8);
        transform: scale(1.1);
      }
    }
  `;
  document.head.appendChild(styleElement);
}

const drawerWidth = 280;

export default function Layout({ children }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const router = useRouter();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const menuItems = [
    { text: '股票分析', icon: <AssessmentIcon />, path: '/analysis', gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)' },
    { text: '回测', icon: <ChartIcon />, path: '/backtest', gradient: 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)' },
    { text: '圆桌', icon: <PeopleIcon />, path: '/round-table', gradient: 'linear-gradient(135deg, #22c55e 0%, #4ade80 100%)' },
    { text: '历史', icon: <HistoryIcon />, path: '/history', gradient: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)' },
    { text: '设置', icon: <SettingsIcon />, path: '/settings', gradient: 'linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%)' },
  ];

  const drawer = (
    <Box 
      sx={{ 
        height: '100%',
        background: 'linear-gradient(180deg, rgba(26, 26, 46, 0.95) 0%, rgba(15, 15, 35, 0.98) 100%)',
        backdropFilter: 'blur(20px)',
        borderRight: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    > {/* Logo和品牌区域 */}
    <Box sx={{ 
      py: 3, 
      px: 2,
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
      borderRadius: '0 0 20px 20px',
      margin: '0 16px 20px 16px',
      border: '1px solid rgba(99, 102, 241, 0.2)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* 背景装饰 */}
      <Box sx={{
        position: 'absolute',
        top: -50,
        right: -50,
        width: 100,
        height: 100,
        background: 'radial-gradient(circle, rgba(99, 102, 241, 0.2) 0%, transparent 70%)',
        borderRadius: '50%',
        animation: 'float 6s ease-in-out infinite',
      }} />
      
      <Avatar sx={{ 
        width: 50, 
        height: 50, 
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        mb: 1,
        fontSize: '1.5rem',
        boxShadow: '0 8px 25px rgba(99, 102, 241, 0.4)',
      }}>
        🏦
      </Avatar>
      
      <Typography 
        variant="h6" 
        component="div" 
        sx={{ 
          fontWeight: 700,
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          textAlign: 'center',
          fontSize: '1.1rem',
        }}
      >
        AI投资助手
      </Typography>
      <Typography 
        variant="body2" 
        sx={{ 
          color: 'text.secondary',
          textAlign: 'center',
          fontSize: '0.75rem',
          mt: 0.5,
        }}
      >
        价值投资分析平台
      </Typography>
    </Box>

      {/* 导航菜单 */}
      <List sx={{ px: 2 }}>
        {menuItems.map((item, index) => (
          <Link key={item.text} href={item.path} passHref legacyBehavior>
            <ListItem 
              button 
              component="a"
              selected={router.pathname === item.path}
              sx={{
                my: 1,
                borderRadius: 2,
                position: 'relative',
                overflow: 'hidden',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                background: router.pathname === item.path 
                  ? item.gradient
                  : 'transparent',
                color: router.pathname === item.path ? 'white' : 'rgba(255, 255, 255, 0.9)',
                '&:hover': {
                  background: router.pathname === item.path 
                    ? item.gradient
                    : 'rgba(99, 102, 241, 0.15)',
                  transform: 'translateX(8px) scale(1.02)',
                  boxShadow: router.pathname === item.path
                    ? '0 8px 25px rgba(99, 102, 241, 0.3)'
                    : '0 4px 15px rgba(99, 102, 241, 0.2)',
                  color: 'white',
                },
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  bottom: 0,
                  width: 4,
                  background: router.pathname === item.path ? 'white' : 'transparent',
                  borderRadius: '0 2px 2px 0',
                  transition: 'all 0.3s ease',
                },
                // 添加动画延迟让菜单项依次出现
                animation: `fadeInUp 0.6s ease ${index * 0.1}s both`,
              }}
              onClick={() => isMobile && handleDrawerToggle()}
            >
              <ListItemIcon sx={{ 
                minWidth: 45,
                color: 'inherit',
                '& .MuiSvgIcon-root': {
                  fontSize: '1.3rem',
                  filter: router.pathname === item.path 
                    ? 'drop-shadow(0 2px 4px rgba(255,255,255,0.3))'
                    : 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))'
                }
              }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text} 
                primaryTypographyProps={{
                  fontWeight: router.pathname === item.path ? 600 : 500,
                  fontSize: '0.9rem',
                  color: 'inherit',
                  textShadow: router.pathname === item.path 
                    ? 'none' 
                    : '0 1px 2px rgba(0,0,0,0.3)',
                }}
              />
              
              {/* 选中状态的右侧指示器 */}
              {router.pathname === item.path && (
                <Box sx={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: 'white',
                  boxShadow: '0 0 10px rgba(255,255,255,0.8)',
                  animation: 'pulse-glow 2s ease-in-out infinite',
                }} />
              )}
            </ListItem>
          </Link>
        ))}
      </List>

      {/* 底部装饰 */}
      <Box sx={{ 
        position: 'absolute',
        bottom: 20,
        left: 20,
        right: 20,
        textAlign: 'center',
        py: 2,
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
        borderRadius: 2,
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}>
        <Typography variant="caption" sx={{ 
          color: 'rgba(255, 255, 255, 0.7)', 
          fontSize: '0.7rem',
          textShadow: '0 1px 2px rgba(0,0,0,0.3)',
        }}>
          © 2024 AI投资助手
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* 顶部导航栏 */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => isMobile ? theme.zIndex.drawer : theme.zIndex.drawer + 1,
          background: 'linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(51, 65, 85, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          border: 'none',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 8px 25px rgba(0, 0, 0, 0.3)',
        }}
      >
        <Toolbar sx={{ minHeight: '70px !important' }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ 
              mr: 2, 
              display: { md: 'none' },
              background: 'rgba(99, 102, 241, 0.1)',
              '&:hover': {
                background: 'rgba(99, 102, 241, 0.2)',
                transform: 'scale(1.1)',
              },
              transition: 'all 0.2s ease',
            }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography 
            variant="h6" 
            noWrap 
            component="div" 
            sx={{ 
              flexGrow: 1,
              fontWeight: 600,
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            {menuItems.find(item => item.path === router.pathname)?.text || 'Hedge Fund AI'}
          </Typography>

          {/* 状态指示器 */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #22c55e 0%, #4ade80 100%)',
              boxShadow: '0 0 10px rgba(34, 197, 94, 0.5)',
              animation: 'pulse-glow 2s ease-in-out infinite',
            }} />
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.75rem' }}>
              在线
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      {/* 侧边栏 */}
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={isMobile ? mobileOpen : true}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth, 
              borderRight: 'none', 
              border: 'none',
              boxShadow: isMobile ? '0 25px 50px -12px rgba(0, 0, 0, 0.4)' : 'none',
              background: 'transparent',
              zIndex: isMobile ? (theme) => theme.zIndex.modal : 'auto',
            },
            zIndex: isMobile ? (theme) => theme.zIndex.modal : 'auto',
          }}
        >
          {drawer}
        </Drawer>
      </Box>

      {/* 主要内容区域 */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 3 },
          width: { md: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          pt: { xs: 10, md: 12 },
          background: 'transparent',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.02) 0%, rgba(139, 92, 246, 0.02) 50%, rgba(236, 72, 153, 0.02) 100%)',
            pointerEvents: 'none',
            zIndex: -1,
          }
        }}
      >
        {children}
      </Box>
    </Box>
  );
} 