import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import ReportProgress from '../ReportProgress';

const mockStore = configureStore([]);

describe('ReportProgress Component', () => {
  it('renders nothing when not generating', () => {
    const store = mockStore({
      report: {
        reportGenerationStatus: {
          isGenerating: false,
          progress: 0,
          statusMessage: '',
        },
      },
    });

    const { container } = render(
      <Provider store={store}>
        <ReportProgress />
      </Provider>
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders progress when generating', () => {
    const store = mockStore({
      report: {
        reportGenerationStatus: {
          isGenerating: true,
          progress: 45,
          statusMessage: '데이터 분석 중...',
        },
      },
    });

    render(
      <Provider store={store}>
        <ReportProgress />
      </Provider>
    );

    expect(screen.getByText('리포트 생성 중')).toBeInTheDocument();
    expect(screen.getByText('데이터 분석 중...')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
  });
});
