import React from 'react';
import { render, screen } from '@testing-library/react';
import LoadingButton from '../LoadingButton';

describe('LoadingButton', () => {
  test('renders button with children when not loading', () => {
    render(<LoadingButton>Click Me</LoadingButton>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  test('renders loading spinner when loading', () => {
    render(<LoadingButton loading>Click Me</LoadingButton>);
    expect(screen.queryByText('Click Me')).not.toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('is disabled when loading', () => {
    render(<LoadingButton loading>Click Me</LoadingButton>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  test('is disabled when disabled prop is true', () => {
    render(<LoadingButton disabled>Click Me</LoadingButton>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
