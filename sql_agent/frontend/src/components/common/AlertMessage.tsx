import React, { useState, useEffect } from 'react';
import { Alert, AlertProps, Snackbar } from '@mui/material';

interface AlertMessageProps extends AlertProps {
  message: string;
  open: boolean;
  onClose?: () => void;
  autoHideDuration?: number;
}

const AlertMessage: React.FC<AlertMessageProps> = ({
  message,
  open,
  onClose,
  autoHideDuration = 6000,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(open);

  useEffect(() => {
    setIsOpen(open);
  }, [open]);

  const handleClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setIsOpen(false);
    if (onClose) {
      onClose();
    }
  };

  return (
    <Snackbar
      open={isOpen}
      autoHideDuration={autoHideDuration}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
    >
      <Alert onClose={handleClose} severity={props.severity} sx={{ width: '100%' }}>
        {message}
      </Alert>
    </Snackbar>
  );
};

export default AlertMessage;