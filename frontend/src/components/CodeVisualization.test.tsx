import React from 'react';
import { render, screen } from '@testing-library/react';
import CodeVisualization from './CodeVisualization';

// Mock the PlotlyChart component
jest.mock('./ui/plotly-chart', () => ({
  PlotlyChart: ({ plotConfig }: any) => (
    <div data-testid="mock-plotly-chart">
      Plotly Chart: {plotConfig?.data?.length || 0} data points
    </div>
  )
}));

// Mock the EChartsVisualization component
jest.mock('./DataExploration/EChartsVisualization', () => ({
  __esModule: true,
  default: ({ chartConfig }: any) => (
    <div data-testid="mock-echarts">
      ECharts: {chartConfig ? 'Has config' : 'No config'}
    </div>
  )
}));

describe('CodeVisualization Component', () => {
  // Test with Plotly figure
  test('renders Plotly chart when figure is provided', () => {
    const mockFigure = {
      data: [{ x: [1, 2, 3], y: [1, 2, 3], type: 'scatter' }],
      layout: { title: 'Test Plot' }
    };
    
    render(
      <CodeVisualization
        code="console.log('test')"
        figure={mockFigure}
      />
    );
    
    // Check if Plotly chart is rendered
    expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument();
    expect(screen.getByText('Plotly Chart: 1 data points')).toBeInTheDocument();
  });
  
  // Test with ECharts config
  test('renders ECharts when echartsConfig is provided', () => {
    const mockEchartsConfig = {
      title: { text: 'Test Chart' },
      series: [{ type: 'bar', data: [1, 2, 3] }]
    };
    
    render(
      <CodeVisualization
        code="console.log('test')"
        echartsConfig={mockEchartsConfig}
      />
    );
    
    // Check if ECharts is rendered
    expect(screen.getByTestId('mock-echarts')).toBeInTheDocument();
    expect(screen.getByText('ECharts: Has config')).toBeInTheDocument();
  });
  
  // Test with both Plotly and ECharts
  test('renders both charts when both configs are provided', () => {
    const mockFigure = {
      data: [{ x: [1, 2, 3], y: [1, 2, 3], type: 'scatter' }],
      layout: { title: 'Test Plot' }
    };
    
    const mockEchartsConfig = {
      title: { text: 'Test Chart' },
      series: [{ type: 'bar', data: [1, 2, 3] }]
    };
    
    render(
      <CodeVisualization
        code="console.log('test')"
        figure={mockFigure}
        echartsConfig={mockEchartsConfig}
      />
    );
    
    // Check if both charts are rendered
    expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument();
    expect(screen.getByTestId('mock-echarts')).toBeInTheDocument();
  });
  
  // Test with no visualization
  test('does not render charts when no configs are provided', () => {
    render(
      <CodeVisualization
        code="console.log('test')"
      />
    );
    
    // Check that no charts are rendered
    expect(screen.queryByTestId('mock-plotly-chart')).not.toBeInTheDocument();
    expect(screen.queryByTestId('mock-echarts')).not.toBeInTheDocument();
  });
  
  // Test with empty figure
  test('handles empty figure gracefully', () => {
    const emptyFigure = { data: [], layout: {} };
    
    render(
      <CodeVisualization
        code="console.log('test')"
        figure={emptyFigure}
      />
    );
    
    // Check if Plotly chart is rendered with empty data
    expect(screen.getByTestId('mock-plotly-chart')).toBeInTheDocument();
    expect(screen.getByText('Plotly Chart: 0 data points')).toBeInTheDocument();
  });
});
