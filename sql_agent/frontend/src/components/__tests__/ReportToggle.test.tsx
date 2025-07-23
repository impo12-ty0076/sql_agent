import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import ReportToggle from '../ReportToggle';
import { toggleReportGeneration, updateReportOptions } from '../../store/slices/reportSlice';

const mockStore = configureStore([]);

describe('ReportToggle Component', () => {
  let store: any;
  
  beforeEach(() => {
    store = mockStore({
      report: {
        reportGenerationEnabled: false,
        reportGenerationOptions: {
          visualizationTypes: ['bar', 'line'],
          includeInsights: true,
        },
      },
    });
    
    store.dispatch = jest.fn();
  });
  
  it('renders correctly when disabled', () => {
    render(
      <Provider store={store}>
        <ReportToggle />
      </Provider>
    );
    
    expect(screen.getByText('리포트 생성 활성화')).toBeInTheDocument();
    expect(screen.queryByText('리포트 옵션')).not.toBeInTheDocument();
  });
  
  it('renders options when enabled', () => {
    store = mockStore({
      report: {
        reportGenerationEnabled: true,
        reportGenerationOptions: {
          visualizationTypes: ['bar', 'line'],
          includeInsights: true,
        },
      },
    });
    
    render(
      <Provider store={store}>
        <ReportToggle />
      </Provider>
    );
    
    expect(screen.getByText('리포트 생성 활성화')).toBeInTheDocument();
    expect(screen.getByText('리포트 옵션')).toBeInTheDocument();
    expect(screen.getByText('인사이트 포함')).toBeInTheDocument();
    expect(screen.getByLabelText('시각화 유형')).toBeInTheDocument();
  });
  
  it('dispatches toggleReportGeneration when switch is clicked', () => {
    render(
      <Provider store={store}>
        <ReportToggle />
      </Provider>
    );
    
    fireEvent.click(screen.getByRole('checkbox'));
    
    expect(store.dispatch).toHaveBeenCalledWith(toggleReportGeneration(true));
  });
  
  it('dispatches updateReportOptions when insights checkbox is clicked', () => {
    store = mockStore({
      report: {
        reportGenerationEnabled: true,
        reportGenerationOptions: {
          visualizationTypes: ['bar', 'line'],
          includeInsights: true,
        },
      },
    });
    
    render(
      <Provider store={store}>
        <ReportToggle />
      </Provider>
    );
    
    fireEvent.click(screen.getByLabelText('인사이트 포함'));
    
    expect(store.dispatch).toHaveBeenCalledWith(updateReportOptions({ includeInsights: false }));
  });
});