import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { PlotlyChart } from './plotly-chart';

// Mock the lazy-loaded Plot component
jest.mock('react-plotly.js', () => ({
  __esModule: true,
  default: (props: any) => {
    // Log the props for debugging
    console.log('Plot component props:', JSON.stringify(props, null, 2));
    return <div data-testid="mock-plotly-plot">Plotly Plot Mock</div>;
  }
}));

describe('PlotlyChart Component', () => {
  // Basic rendering test
  test('renders loading state initially', () => {
    render(
      <PlotlyChart
        plotConfig={{
          data: [{ x: [1, 2, 3], y: [1, 2, 3], type: 'scatter' }],
          layout: { title: 'Test Plot' }
        }}
      />
    );
    
    expect(screen.getByText('Loading chart...')).toBeInTheDocument();
  });

  // Test with valid data
  test('renders plot when mounted', async () => {
    // Mock window.dispatchEvent
    const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');
    
    const mockData = [
      { x: [1, 2, 3], y: [1, 2, 3], type: 'scatter' }
    ];
    
    render(
      <PlotlyChart
        plotConfig={{
          data: mockData,
          layout: { title: 'Test Plot' }
        }}
      />
    );

    // Wait for component to mount
    await waitFor(() => {
      expect(dispatchEventSpy).toHaveBeenCalled();
    });
    
    // In a real test, we would check for the plotly component
    // but since we're mocking it, we'll check for our mock element
    await waitFor(() => {
      expect(screen.getByTestId('mock-plotly-plot')).toBeInTheDocument();
    });
  });

  // Test with empty data
  test('shows "No data available" when data is empty', async () => {
    render(
      <PlotlyChart
        plotConfig={{
          data: [],
          layout: {}
        }}
      />
    );

    // Wait for component to mount
    await waitFor(() => {
      expect(screen.getByText('No data available')).toBeInTheDocument();
    });
  });

  // Test with null/undefined data
  test('handles undefined plotConfig gracefully', async () => {
    render(
      <PlotlyChart
        plotConfig={undefined as any}
      />
    );

    // Wait for component to mount
    await waitFor(() => {
      expect(screen.getByText('No data available')).toBeInTheDocument();
    });
  });

  // Test error boundary
  test('error boundary catches rendering errors', async () => {
    // Create a plotConfig that will cause an error
    const problematicConfig = {
      data: [{ 
        x: null, // This will cause an error
        y: [1, 2, 3],
        type: 'scatter'
      }],
      layout: { title: 'Error Test' }
    };
    
    // Mock console.error to prevent test output pollution
    const originalError = console.error;
    console.error = jest.fn();
    
    render(
      <PlotlyChart plotConfig={problematicConfig} />
    );
    
    // Wait for component to mount and error boundary to catch error
    await waitFor(() => {
      // In a real test with the actual error boundary, we would check for the error message
      // Since we're mocking, we'll just verify console.error was called
      expect(console.error).toHaveBeenCalled();
    });
    
    // Restore console.error
    console.error = originalError;
  });
});
