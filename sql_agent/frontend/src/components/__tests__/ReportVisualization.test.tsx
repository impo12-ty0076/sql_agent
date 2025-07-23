import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import ReportVisualization from '../ReportVisualization';

const mockStore = configureStore([]);

describe('ReportVisualization Component', () => {
  it('renders message when no report is available', () => {
    const store = mockStore({
      report: {
        currentReport: null,
        error: null,
      },
    });
    
    render(
      <Provider store={store}>
        <ReportVisualization />
      </Provider>
    );
    
    expect(screen.getByText('리포트가 생성되지 않았습니다. 쿼리를 실행하고 리포트 생성 옵션을 활성화하세요.')).toBeInTheDocument();
  });
  
  it('renders error message when there is an error', () => {
    const store = mockStore({
      report: {
        currentReport: null,
        error: '리포트 생성에 실패했습니다.',
      },
    });
    
    render(
      <Provider store={store}>
        <ReportVisualization />
      </Provider>
    );
    
    expect(screen.getByText('리포트 생성 오류')).toBeInTheDocument();
    expect(screen.getByText('리포트 생성에 실패했습니다.')).toBeInTheDocument();
  });
  
  it('renders report visualizations and insights', () => {
    const mockReport = {
      id: 'report-1',
      resultId: 'result-1',
      visualizations: [
        {
          id: 'viz-1',
          type: 'bar',
          title: '월별 매출',
          description: '2023년 월별 매출 추이',
          imageData: 'data:image/png;base64,abc123',
        },
      ],
      insights: [
        '8월에 가장 높은 매출을 기록했습니다.',
        '주말 매출이 평일보다 30% 높습니다.',
      ],
      createdAt: '2023-09-15T10:30:00Z',
    };
    
    const store = mockStore({
      report: {
        currentReport: mockReport,
        error: null,
      },
    });
    
    // Mock document.createElement and other DOM methods
    const mockCreateElement = jest.fn().mockReturnValue({
      href: '',
      download: '',
      click: jest.fn(),
    });
    const mockAppendChild = jest.fn();
    const mockRemoveChild = jest.fn();
    
    document.createElement = mockCreateElement;
    document.body.appendChild = mockAppendChild;
    document.body.removeChild = mockRemoveChild;
    
    render(
      <Provider store={store}>
        <ReportVisualization />
      </Provider>
    );
    
    expect(screen.getByText('데이터 분석 리포트')).toBeInTheDocument();
    expect(screen.getByText('월별 매출')).toBeInTheDocument();
    expect(screen.getByText('2023년 월별 매출 추이')).toBeInTheDocument();
    expect(screen.getByText('8월에 가장 높은 매출을 기록했습니다.')).toBeInTheDocument();
    expect(screen.getByText('주말 매출이 평일보다 30% 높습니다.')).toBeInTheDocument();
    
    // Test download functionality
    fireEvent.click(screen.getByText('리포트 다운로드'));
    expect(mockCreateElement).toHaveBeenCalledWith('a');
    expect(mockAppendChild).toHaveBeenCalled();
    expect(mockRemoveChild).toHaveBeenCalled();
  });
});