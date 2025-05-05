import React from 'react';
import { render, screen } from '@testing-library/react';
import ChartErrorBoundary from './ChartErrorBoundary';
import '@testing-library/jest-dom';

// Create a component that throws an error
const ErrorComponent = () => {
  throw new Error('Test error');
};

// Create a component that doesn't throw an error
const NormalComponent = () => {
  return <div>Normal component</div>;
};

describe('ChartErrorBoundary Component', () => {
  // Suppress console.error during tests
  const originalConsoleError = console.error;
  
  beforeAll(() => {
    console.error = jest.fn();
  });
  
  afterAll(() => {
    console.error = originalConsoleError;
  });
  
  test('renders children when no error occurs', () => {
    render(
      <ChartErrorBoundary>
        <NormalComponent />
      </ChartErrorBoundary>
    );
    
    // Check if the normal component is rendered
    expect(screen.getByText('Normal component')).toBeInTheDocument();
  });
  
  test('renders error UI when an error occurs', () => {
    // We need to mock the console.error to prevent the test from failing due to the error
    const spy = jest.spyOn(console, 'error');
    spy.mockImplementation(() => {});
    
    render(
      <ChartErrorBoundary>
        <ErrorComponent />
      </ChartErrorBoundary>
    );
    
    // Check if the error UI is rendered
    expect(screen.getByText('Chart Rendering Error')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong while rendering this specific chart.')).toBeInTheDocument();
    expect(screen.getByText(/Error: Test error/)).toBeInTheDocument();
    
    // Restore the console.error
    spy.mockRestore();
  });
  
  test('includes chart title in error UI when provided', () => {
    // We need to mock the console.error to prevent the test from failing due to the error
    const spy = jest.spyOn(console, 'error');
    spy.mockImplementation(() => {});
    
    render(
      <ChartErrorBoundary chartTitle="Test Chart">
        <ErrorComponent />
      </ChartErrorBoundary>
    );
    
    // Check if the chart title is included in the error UI
    expect(screen.getByText('Test Chart - Error')).toBeInTheDocument();
    
    // Restore the console.error
    spy.mockRestore();
  });
  
  test('logs error details to console', () => {
    // We need to mock the console.error to check if it's called
    const spy = jest.spyOn(console, 'error');
    spy.mockImplementation(() => {});
    
    render(
      <ChartErrorBoundary>
        <ErrorComponent />
      </ChartErrorBoundary>
    );
    
    // Check if console.error was called with the error details
    expect(spy).toHaveBeenCalled();
    expect(spy.mock.calls[0][0]).toBe('ChartErrorBoundary caught an error:');
    
    // Restore the console.error
    spy.mockRestore();
  });
});
