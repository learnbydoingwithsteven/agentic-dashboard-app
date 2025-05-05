import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Page from './page';
import '@testing-library/jest-dom';

// Mock the components used in the page
jest.mock('@/components/ApiKeySettings', () => ({
  ApiKeySettings: ({ onApiKeySaved }: { onApiKeySaved: (apiKey: string, useOllama: boolean) => void }) => (
    <div data-testid="api-key-settings">
      <button onClick={() => onApiKeySaved('test-api-key', false)}>Save API Key</button>
      <button onClick={() => onApiKeySaved('', true)}>Use Ollama</button>
    </div>
  ),
  getApiKey: () => 'test-api-key',
  getUseOllama: () => false,
}));

jest.mock('@/components/AgentConversationMonitor', () => ({
  AgentConversationMonitor: ({ logs }: { logs: any[] }) => (
    <div data-testid="agent-conversation-monitor">
      Agent Logs: {logs.length}
    </div>
  ),
}));

jest.mock('@/components/DataExploration/DataExplorationPageDebug', () => ({
  __esModule: true,
  default: ({ apiKey, useOllama, onBack }: { apiKey: string, useOllama: boolean, onBack: () => void }) => (
    <div data-testid="data-exploration-page">
      Data Exploration Page
      <div>API Key: {apiKey}</div>
      <div>Use Ollama: {useOllama.toString()}</div>
      <button onClick={onBack}>Back</button>
    </div>
  ),
}));

jest.mock('@/components/CodeVisualization', () => ({
  CodeVisualization: ({ code, figure, echartsConfig }: { code: string, figure?: any, echartsConfig?: any }) => (
    <div data-testid="code-visualization">
      Code Visualization
      <div>Has Figure: {figure ? 'Yes' : 'No'}</div>
      <div>Has ECharts Config: {echartsConfig ? 'Yes' : 'No'}</div>
    </div>
  ),
}));

// Mock fetch
global.fetch = jest.fn();

describe('Page Component', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    
    // Mock successful API responses
    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/check_api_key')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            available_models: {
              'llama3-70b-8192': 'Groq LLaMA 3 70B',
              'mixtral-8x7b-32768': 'Groq Mixtral 8x7B',
            },
          }),
        });
      }
      if (url.includes('/api/admin/logs')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            logs: [
              {
                timestamp: '2023-01-01T12:00:00Z',
                messages: [
                  { name: 'Data_Analyst', content: 'Test message', role: 'assistant' },
                ],
              },
            ],
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });
  
  test('renders the main page with API key settings', async () => {
    render(<Page />);
    
    // Check if the API key settings component is rendered
    expect(screen.getByTestId('api-key-settings')).toBeInTheDocument();
    
    // Check if the title is rendered
    expect(screen.getByText('Agentic Data Visualization')).toBeInTheDocument();
  });
  
  test('switches between agent visualizations and data exploration views', async () => {
    render(<Page />);
    
    // Initially in agent visualizations view
    expect(screen.queryByTestId('data-exploration-page')).not.toBeInTheDocument();
    
    // Click the data exploration button
    fireEvent.click(screen.getByText('Data Exploration'));
    
    // Check if the data exploration page is rendered
    expect(screen.getByTestId('data-exploration-page')).toBeInTheDocument();
    
    // Click the back button
    fireEvent.click(screen.getByText('Back'));
    
    // Check if we're back to the agent visualizations view
    expect(screen.queryByTestId('data-exploration-page')).not.toBeInTheDocument();
  });
  
  test('saves API key and fetches available models', async () => {
    render(<Page />);
    
    // Click the save API key button
    fireEvent.click(screen.getByText('Save API Key'));
    
    // Wait for the API call to complete
    await waitFor(() => {
      // Check if fetch was called with the right URL
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/check_api_key'),
        expect.any(Object)
      );
    });
  });
  
  test('fetches admin logs', async () => {
    render(<Page />);
    
    // Wait for the API call to complete
    await waitFor(() => {
      // Check if fetch was called with the right URL
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/logs'),
        expect.any(Object)
      );
      
      // Check if the agent logs are rendered
      expect(screen.getByText('Agent Logs: 1')).toBeInTheDocument();
    });
  });
  
  test('handles errors gracefully', async () => {
    // Mock a failed API response
    (global.fetch as jest.Mock).mockImplementationOnce(() => {
      return Promise.reject(new Error('API error'));
    });
    
    // Mock console.error to prevent test output pollution
    const originalError = console.error;
    console.error = jest.fn();
    
    render(<Page />);
    
    // Wait for the API call to complete
    await waitFor(() => {
      // Check if console.error was called
      expect(console.error).toHaveBeenCalled();
    });
    
    // Restore console.error
    console.error = originalError;
  });
});
