import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Badge,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Brightness4,
  Brightness7,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store';
import { toggleSidebar, toggleTheme } from '../../store/slices/uiSlice';
import UserMenu from '../auth/UserMenu';
import PermissionGuard from '../auth/PermissionGuard';

// Define the notification interface to match the one in uiSlice.ts
interface AppNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: string;
  read: boolean;
}

interface HeaderProps {
  title: string;
}

const Header: React.FC<HeaderProps> = ({ title }) => {
  const dispatch = useDispatch();
  const { theme } = useSelector((state: RootState) => state.ui);
  const notifications = useSelector(
    (state: RootState) => state.ui.notifications as AppNotification[]
  );

  const [notificationAnchorEl, setNotificationAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleNotificationMenuClose = () => {
    setNotificationAnchorEl(null);
  };

  const handleThemeToggle = () => {
    dispatch(toggleTheme());
  };

  // Get unread notifications count
  const unreadNotifications = Array.isArray(notifications)
    ? notifications.filter((n: AppNotification) => !n.read).length
    : 0;

  return (
    <AppBar position="static">
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          aria-label="menu"
          sx={{ mr: 2 }}
          onClick={() => dispatch(toggleSidebar())}
        >
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          {title}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
            <IconButton color="inherit" onClick={handleThemeToggle}>
              {theme === 'light' ? <Brightness4 /> : <Brightness7 />}
            </IconButton>
          </Tooltip>

          <PermissionGuard>
            <Tooltip title="알림">
              <IconButton color="inherit" onClick={handleNotificationMenuOpen}>
                <Badge badgeContent={unreadNotifications} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>
          </PermissionGuard>

          <UserMenu />
        </Box>

        <Menu
          id="notification-menu"
          anchorEl={notificationAnchorEl}
          keepMounted
          open={Boolean(notificationAnchorEl)}
          onClose={handleNotificationMenuClose}
        >
          {Array.isArray(notifications) && notifications.length > 0 ? (
            notifications.slice(0, 5).map((notification: AppNotification) => (
              <MenuItem key={notification.id} onClick={handleNotificationMenuClose}>
                <Typography variant="body2" color={notification.type}>
                  {notification.message}
                </Typography>
              </MenuItem>
            ))
          ) : (
            <MenuItem onClick={handleNotificationMenuClose}>
              <Typography variant="body2">No notifications</Typography>
            </MenuItem>
          )}
          {Array.isArray(notifications) && notifications.length > 5 && (
            <MenuItem onClick={handleNotificationMenuClose}>
              <Typography variant="body2">View all notifications</Typography>
            </MenuItem>
          )}
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
