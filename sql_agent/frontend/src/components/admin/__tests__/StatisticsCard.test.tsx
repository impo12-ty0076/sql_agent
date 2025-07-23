import React from 'react';
import { render, screen } from '@testing-library/react';
import StatisticsCard from '../StatisticsCard';
import InfoIcon from '@mui/icons-material/Info';

describe('StatisticsCard', () => {
  test('renders title and value correctly', () => {
    render(<StatisticsCard title="Test Title" value="123" />);
    
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('123')).toBeInTheDocument();
  });

  test('renders with icon', () => {
    render(
      <StatisticsCard 
        title="Test Title" 
        value="123" 
        icon={<InfoIcon data-testid="test-icon" />} 
      />
    );
    
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
  });

  test('shows loading state', () => {
    render(<StatisticsCard title="Test Title" value="123" loading={true} />);
    
    expect(screen.queryByText('123')).not.toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('renders with description tooltip', () => {
    render(
      <StatisticsCard 
        title="Test Title" 
        value="123" 
        description="Test Description" 
      />
    );
    
    // InfoIcon should be present when description is provided
    expect(screen.getByTestId('InfoIcon')).toBeInTheDocument();
  });

  test('applies custom color', () => {
    render(<StatisticsCard title="Test Title" value="123" color="error.main" />);
    
    const valueElement = screen.getByText('123');
    expect(valueElement).toHaveStyle('color: error.main');
  });
});