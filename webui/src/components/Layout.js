import { useState } from 'react';
import { Box, AppBar, Toolbar, Typography, Drawer, IconButton, List, ListItem, ListItemIcon, ListItemText, Divider, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { Menu as MenuIcon, Dashboard as DashboardIcon, ShowChart as ChartIcon, Assessment as AssessmentIcon, Settings as SettingsIcon, History as HistoryIcon, People as PeopleIcon } from '@mui/icons-material';
import Link from 'next/link';
import { useRouter } from 'next/router';

const drawerWidth = 240;

export default function Layout({ children }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const router = useRouter();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const menuItems = [
    // { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: '股票分析', icon: <AssessmentIcon />, path: '/analysis' },
    { text: '回测', icon: <ChartIcon />, path: '/backtest' },
    { text: '圆桌', icon: <PeopleIcon />, path: '/round-table' },
    { text: '历史', icon: <HistoryIcon />, path: '/history' },
    { text: '设置', icon: <SettingsIcon />, path: '/settings' },
  ];

  const drawer = (
    <Box>
      <Box sx={{ py: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
          <ChartIcon sx={{ mr: 1 }} /> Hedge Fund AI
        </Typography>
      </Box>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <Link key={item.text} href={item.path} passHref legacyBehavior>
            <ListItem 
              button 
              component="a"
              selected={router.pathname === item.path}
              sx={{
                my: 0.5,
                mx: 1,
                borderRadius: 1,
                '&.Mui-selected': {
                  bgcolor: 'primary.dark',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                  },
                },
              }}
              onClick={() => isMobile && handleDrawerToggle()}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          </Link>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: 'background.paper',
          boxShadow: 1,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {menuItems.find(item => item.path === router.pathname)?.text || 'Hedge Fund AI'}
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={isMobile ? mobileOpen : true}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth, borderRight: 'none', boxShadow: 'none' },
          }}
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          backgroundColor: 'background.default',
          minHeight: '100vh',
          pt: { xs: 8, md: 10 },
        }}
      >
        {children}
      </Box>
    </Box>
  );
} 