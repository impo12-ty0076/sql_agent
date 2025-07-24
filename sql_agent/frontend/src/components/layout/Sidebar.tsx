import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
  Collapse,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  Bookmark as BookmarkIcon,
  ExpandLess,
  ExpandMore,
  Feedback as FeedbackIcon,
  AdminPanelSettings as AdminIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import { useNavigate, useLocation } from 'react-router-dom';
import { setActiveTab } from '../../store/slices/uiSlice';

const Sidebar: React.FC = () => {
  const { sidebarOpen } = useSelector((state: RootState) => state.ui as { sidebarOpen: boolean });
  const { user } = useSelector(
    (state: RootState) => state.auth as { user: { role: string } | null }
  );
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();

  const [queryOpen, setQueryOpen] = React.useState(true);

  const handleNavigation = (path: string) => {
    navigate(path);
    dispatch(setActiveTab(path));
  };

  const handleQueryClick = () => {
    setQueryOpen(!queryOpen);
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={sidebarOpen}
      sx={{
        width: 240,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 240,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" component="div">
          SQL Agent
        </Typography>
      </Box>
      <Divider />
      <List>
        <ListItem button onClick={() => handleNavigation('/')} selected={isActive('/')}>
          <ListItemIcon>
            <DashboardIcon />
          </ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>

        <ListItem button onClick={handleQueryClick}>
          <ListItemIcon>
            <CodeIcon />
          </ListItemIcon>
          <ListItemText primary="Query" />
          {queryOpen ? <ExpandLess /> : <ExpandMore />}
        </ListItem>

        <Collapse in={queryOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            <ListItem
              button
              sx={{ pl: 4 }}
              onClick={() => handleNavigation('/query')}
              selected={isActive('/query')}
            >
              <ListItemIcon>
                <CodeIcon />
              </ListItemIcon>
              <ListItemText primary="New Query" />
            </ListItem>

            <ListItem
              button
              sx={{ pl: 4 }}
              onClick={() => handleNavigation('/history')}
              selected={isActive('/history')}
            >
              <ListItemIcon>
                <HistoryIcon />
              </ListItemIcon>
              <ListItemText primary="History" />
            </ListItem>

            <ListItem
              button
              sx={{ pl: 4 }}
              onClick={() => handleNavigation('/saved')}
              selected={isActive('/saved')}
            >
              <ListItemIcon>
                <BookmarkIcon />
              </ListItemIcon>
              <ListItemText primary="Saved Queries" />
            </ListItem>
          </List>
        </Collapse>

        <ListItem
          button
          onClick={() => handleNavigation('/databases')}
          selected={isActive('/databases')}
        >
          <ListItemIcon>
            <StorageIcon />
          </ListItemIcon>
          <ListItemText primary="Databases" />
        </ListItem>

        <ListItem
          button
          onClick={() => handleNavigation('/feedback')}
          selected={isActive('/feedback')}
        >
          <ListItemIcon>
            <FeedbackIcon />
          </ListItemIcon>
          <ListItemText primary="Feedback" />
        </ListItem>
      </List>

      <Divider />

      <List>
        {user?.role === 'admin' && (
          <ListItem button onClick={() => handleNavigation('/admin')} selected={isActive('/admin')}>
            <ListItemIcon>
              <AdminIcon />
            </ListItemIcon>
            <ListItemText primary="Admin" />
          </ListItem>
        )}

        <ListItem
          button
          onClick={() => handleNavigation('/settings')}
          selected={isActive('/settings')}
        >
          <ListItemIcon>
            <SettingsIcon />
          </ListItemIcon>
          <ListItemText primary="Settings" />
        </ListItem>
      </List>
    </Drawer>
  );
};

export default Sidebar;
