import React, { useState } from 'react';
import {
  Button,
  MenuItem,
  ListItemIcon,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';
import { ExitToApp, Logout as LogoutIcon } from '@mui/icons-material';
import useAuth from '../../hooks/useAuth';

interface LogoutProps {
  variant?: 'button' | 'menuItem';
  onClick?: () => void;
  showConfirmation?: boolean;
}

const Logout: React.FC<LogoutProps> = ({
  variant = 'button',
  onClick,
  showConfirmation = true,
}) => {
  const { logout } = useAuth();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleLogoutClick = () => {
    if (showConfirmation) {
      setConfirmOpen(true);
    } else {
      performLogout();
    }
  };

  const handleConfirmLogout = () => {
    setConfirmOpen(false);
    performLogout();
  };

  const handleCancelLogout = () => {
    setConfirmOpen(false);
  };

  const performLogout = async () => {
    await logout();

    // Call additional onClick handler if provided
    if (onClick) {
      onClick();
    }
  };

  if (variant === 'menuItem') {
    return (
      <>
        <MenuItem onClick={handleLogoutClick}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          로그아웃
        </MenuItem>

        {showConfirmation && (
          <Dialog
            open={confirmOpen}
            onClose={handleCancelLogout}
            aria-labelledby="logout-dialog-title"
            aria-describedby="logout-dialog-description"
          >
            <DialogTitle id="logout-dialog-title">로그아웃 확인</DialogTitle>
            <DialogContent>
              <DialogContentText id="logout-dialog-description">
                정말 로그아웃 하시겠습니까?
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCancelLogout} color="primary">
                취소
              </Button>
              <Button onClick={handleConfirmLogout} color="primary" autoFocus>
                로그아웃
              </Button>
            </DialogActions>
          </Dialog>
        )}
      </>
    );
  }

  return (
    <>
      <Button color="inherit" onClick={handleLogoutClick} startIcon={<ExitToApp />}>
        로그아웃
      </Button>

      {showConfirmation && (
        <Dialog
          open={confirmOpen}
          onClose={handleCancelLogout}
          aria-labelledby="logout-dialog-title"
          aria-describedby="logout-dialog-description"
        >
          <DialogTitle id="logout-dialog-title">로그아웃 확인</DialogTitle>
          <DialogContent>
            <DialogContentText id="logout-dialog-description">
              정말 로그아웃 하시겠습니까?
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCancelLogout} color="primary">
              취소
            </Button>
            <Button onClick={handleConfirmLogout} color="primary" autoFocus>
              로그아웃
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </>
  );
};

export default Logout;
