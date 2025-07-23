import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AlertMessage from '../AlertMessage';

describe('AlertMessage', () => {
  test('renders alert with message when open', () => {
    render(<AlertMessage message="Test alert message" open severity="info" />);
    expect(screen.getByText('Test alert message')).toBeInTheDocument();
  });

  test('does not render alert when not open', () => {
    render(<AlertMessage message="Test alert message" open={false} severity="info" />);
    expect(screen.queryByText('Test alert message')).not.toBeInTheDocument();
  });

  test('calls onClose when close button is clicked', async () => {
    const onClose = jest.fn();
    render(<AlertMessage message="Test alert message" open severity="info" onClose={onClose} />);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    await userEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalled();
  });

  test('renders with different severity levels', () => {
    const { rerender } = render(<AlertMessage message="Error message" open severity="error" />);
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardError');
    
    rerender(<AlertMessage message="Warning message" open severity="warning" />);
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardWarning');
    
    rerender(<AlertMessage message="Info message" open severity="info" />);
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardInfo');
    
    rerender(<AlertMessage message="Success message" open severity="success" />);
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardSuccess');
  });
});