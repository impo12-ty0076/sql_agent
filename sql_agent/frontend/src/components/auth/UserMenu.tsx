import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Tooltip,
  Box,
  Typography,
} from '@mui/material';
import {
  AccountCircle,
  Person,
  Settings,
  AdminPanelSettings,
} from '@mui/icons-material';
import useAuth from '../../hooks/useAuth';
import Logout from './Logout';

const UserMenu: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { user, isAuthenticated, isAdmin } = useAuth();
  const navigate = useNavigate();
  
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };
  
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  
  const handleProfileClick = () => {
    navigate('/profile');
    handleMenuClose();
  };
  
  const handleSettingsClick = () => {
    navigate('/settings');
    handleMenuClose();
  };
  
  const handleAdminClick = () => {
    navigate('/admin');
    handleMenuClose();
  };
  
  if (!isAuthenticated) {
    return (
      <Tooltip title="로그인">
        <IconButton 
          color="inherit" 
          onClick={() => navigate('/login')}
          size="large"
        >
          <AccountCircle />
        </IconButton>
      </Tooltip>
    );
  }
  
  const userInitial = user?.username?.charAt(0).toUpperCase() || 'U';
  
  return (
    <>
      <Tooltip title="계정 설정">
        <IconButton
          onClick={handleMenuOpen}
          size="small"
          sx={{ ml: 2 }}
          aria-controls={Boolean(anchorEl) ? 'account-menu' : undefined}
          aria-haspopup="true"
          aria-expanded={Boolean(anchorEl) ? 'true' : undefined}
        >
          <Avatar 
            sx={{ 
              width: 32, 
              height: 32, 
              bgcolor: 'primary.main',
              color: 'white',
              fontWeight: 'bold'
            }}
          >
            {userInitial}
          </Avatar>
        </IconButton>
      </Tooltip>
      
      <Menu
        anchorEl={anchorEl}
        id="account-menu"
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        onClick={handleMenuClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            width: 220,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle1" noWrap>
            {user?.username}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap>
            {user?.email}
          </Typography>
        </Box>
        
        <Divider />
        
        <MenuItem onClick={handleProfileClick}>
          <ListItemIcon>
            <Person fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="프로필" />
        </MenuItem>
        
        <MenuItem onClick={handleSettingsClick}>
          <ListItemIcon>
            <Settings fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="환경설정" />
        </MenuItem>
        
        {isAdmin && (
          <MenuItem onClick={handleAdminClick}>
            <ListItemIcon>
              <AdminPanelSettings fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="관리자 페이지" />
          </MenuItem>
        )}
        
        <Divider />
        
        <Logout variant="menuItem" />
      </Menu>
    </>
  );
};

export default UserMenu;