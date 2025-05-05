import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ApiKeySettings, getApiKey, getUseOllama } from './ApiKeySettings';
import '@testing-library/jest-dom';

// Mock fetch
global.fetch = jest.fn();

// Mock sessionStorage and localStorage
const mockSessionStorage: Record<string, string> = {};
const mockLocalStorage: Record<string, string> = {};

Object.defineProperty(window, 'sessionStorage', {
  value: {
    getItem: jest.fn((key) => mockSessionStorage[key] || null),
    setItem: jest.fn((key, value) => {
      mockSessionStorage[key] = value;
    }),
    removeItem: jest.fn((key) => {
      delete mockSessionStorage[key];
    }),
    clear: jest.fn(() => {
      Object.keys(mockSessionStorage).forEach((key) => {
        delete mockSessionStorage[key];
      });
    }),
  },
  writable: true,
});

Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: jest.fn((key) => mockLocalStorage[key] || null),
    setItem: jest.fn((key, value) => {
      mockLocalStorage[key] = value;
    }),
    removeItem: jest.fn((key) => {
      delete mockLocalStorage[key];
    }),
    clear: jest.fn(() => {
      Object.keys(mockLocalStorage).forEach((key) => {
        delete mockLocalStorage[key];
      });
    }),
  },
  writable: true,
});

describe('ApiKeySettings Component', () => {
  const mockOnApiKeySaved = jest.fn();
  
  beforeEach(() => {
    // Clear mocks before each test
    jest.clearAllMocks();
    mockSessionStorage['groq_api_key'] = '';
    mockLocalStorage['use_ollama'] = '';
  });
  
  test('renders with default state', () => {
    render(<ApiKeySettings onApiKeySaved={mockOnApiKeySaved} />);
    
    // Check if the component renders with the correct title
    expect(screen.getByText('Model Settings')).toBeInTheDocument();
    
    // Check if the Groq API key input is present
    expect(screen.getByPlaceholderText('Enter your Groq API key')).toBeInTheDocument();
    
    // Check if the Ollama switch is present
    expect(screen.getByText('Use Ollama')).toBeInTheDocument();
    
    // Check if the Save button is disabled initially (no API key and not using Ollama)
    expect(screen.getByText('Save Settings')).toBeDisabled();
  });
  
  test('loads saved API key from sessionStorage', () => {
    // Set up sessionStorage with a saved API key
    mockSessionStorage['groq_api_key'] = 'test-api-key';
    
    render(<ApiKeySettings onApiKeySaved={mockOnApiKeySaved} />);
    
    // Check if the API key input has the saved value
    const apiKeyInput = screen.getByPlaceholderText('Enter your Groq API key') as HTMLInputElement;
    expect(apiKeyInput.value).toBe('test-api-key');
    
    // Check if the component shows as saved
    expect(screen.getByText('Settings Saved')).toBeInTheDocument();
  });
  
  test('loads saved Ollama setting from localStorage', () => {
    // Set up localStorage with Ollama enabled
    mockLocalStorage['use_ollama'] = 'true';
    
    render(<ApiKeySettings onApiKeySaved={mockOnApiKeySaved} />);
    
    // Check if the Ollama switch is checked
    const ollamaSwitch = screen.getByRole('switch') as HTMLInputElement;
    expect(ollamaSwitch.checked).toBe(true);
    
    // Check if the API key input is not shown when Ollama is enabled
    expect(screen.queryByPlaceholderText('Enter your Groq API key')).not.toBeInTheDocument();
  });
  
  test('toggles between Groq and Ollama modes', () => {
    render(<ApiKeySettings onApiKeySaved={mockOnApiKeySaved} />);
    
    // Initially in Groq mode
    expect(screen.getByPlaceholderText('Enter your Groq API key')).toBeInTheDocument();
    
    // Toggle to Ollama mode
    const ollamaSwitch = screen.getByRole('switch');
    fireEvent.click(ollamaSwitch);
    
    // Check if API key input is hidden in Ollama mode
    expect(screen.queryByPlaceholderText('Enter your Groq API key')).not.toBeInTheDocument();
    
    // Toggle back to Groq mode
    fireEvent.click(ollamaSwitch);
    
    // Check if API key input is shown again
    expect(screen.getByPlaceholderText('Enter your Groq API key')).toBeInTheDocument();
  });
  
  test('validates and saves Groq API key', async () => {
    // Mock successful API key validation
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'success',
        message: 'API key is valid',
        available_models: { 'llama3-70b-8192': 'Groq LLaMA 3 70B' }
      })
    });
    
    render(<ApiKeySettings onApiKeySaved={mockOnApiKeySaved} />);
    
    // Enter an API key
    const apiKeyInput = screen.getByPlaceholderText('Enter your Groq API key');
    fireEvent.change(apiKeyInput, { target: { value: 'test-api-key' } });
    
    // Click the save button
    const saveButton = screen.getByText('Save Settings');
    fireEvent.click(saveButton);
    
    // Check if validation is in progress
    expect(screen.getByText('Validating...')).toBeInTheDocument();
    
    // Wait for validation to complete
    await waitFor(() => {
      expect(screen.getByText('Settings Saved')).toBeInTheDocument();
    });
    
    // Check if the API key was saved to sessionStorage
    expect(mockSessionStorage['groq_api_key']).toBe('test-api-key');
    
    // Check if the callback was called with the right parameters
    expect(mockOnApiKeySaved).toHaveBeenCalledWith('test-api-key', false);
    
    // Check if fetch was called with the right parameters
    expect(global.fetch).toHaveBeenCalledWith('http://localhost:5001/api/check_api_key', {
      method: 'GET',
      headers: {
        'X-API-KEY': 'test-api-key',
        'USE-OLLAMA': 'false'
      }
    });
  });
  
  test('validates and saves Ollama setting', async () => {
    // Mock successful Ollama validation
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'success',
        message: 'Ollama is available',
        available_models: { 'ollama:llama3': 'Ollama: llama3' }
      })
    });
    
    render(<ApiKeySettings onApiKeySaved={mockOnApiKeySaved} />);
    
    // Enable Ollama
    const ollamaSwitch = screen.getByRole('switch');
    fireEvent.click(ollamaSwitch);
    
    // Click the save button
    const saveButton = screen.getByText('Save Settings');
    fireEvent.click(saveButton);
    
    // Wait for validation to complete
    await waitFor(() => {
      expect(screen.getByText('Settings Saved')).toBeInTheDocument();
    });
    
    // Check if the Ollama setting was saved to localStorage
    expect(mockLocalStorage['use_ollama']).toBe('true');
    
    // Check if the callback was called with the right parameters
    expect(mockOnApiKeySaved).toHaveBeenCalledWith('', true);
    
    // Check if fetch was called with the right parameters
    expect(global.fetch).toHaveBeenCalledWith('http://localhost:5001/api/check_api_key', {
      method: 'GET',
      headers: {
        'USE-OLLAMA': 'true'
      }
    });
  });
  
  test('handles validation error', async () => {
    // Mock failed API key validation
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({
        status: 'error',
        message: 'Invalid API key'
      })
    });
    
    render(<ApiKeySettings onApiKeySaved={mockOnApiKeySaved} />);
    
    // Enter an API key
    const apiKeyInput = screen.getByPlaceholderText('Enter your Groq API key');
    fireEvent.change(apiKeyInput, { target: { value: 'invalid-api-key' } });
    
    // Click the save button
    const saveButton = screen.getByText('Save Settings');
    fireEvent.click(saveButton);
    
    // Wait for validation to complete
    await waitFor(() => {
      expect(screen.getByText('Invalid API key')).toBeInTheDocument();
    });
    
    // Check if the callback was not called
    expect(mockOnApiKeySaved).not.toHaveBeenCalled();
  });
  
  test('handles network error during validation', async () => {
    // Mock network error
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
    
    render(<ApiKeySettings onApiKeySaved={mockOnApiKeySaved} />);
    
    // Enter an API key
    const apiKeyInput = screen.getByPlaceholderText('Enter your Groq API key');
    fireEvent.change(apiKeyInput, { target: { value: 'test-api-key' } });
    
    // Click the save button
    const saveButton = screen.getByText('Save Settings');
    fireEvent.click(saveButton);
    
    // Wait for validation to complete
    await waitFor(() => {
      expect(screen.getByText('Failed to validate API key. Please check your connection.')).toBeInTheDocument();
    });
    
    // Check if the callback was not called
    expect(mockOnApiKeySaved).not.toHaveBeenCalled();
  });
  
  test('getApiKey utility function returns the saved API key', () => {
    // Set up sessionStorage with a saved API key
    mockSessionStorage['groq_api_key'] = 'test-api-key';
    
    // Call the utility function
    const apiKey = getApiKey();
    
    // Check if it returns the correct value
    expect(apiKey).toBe('test-api-key');
  });
  
  test('getUseOllama utility function returns the saved Ollama setting', () => {
    // Set up localStorage with Ollama enabled
    mockLocalStorage['use_ollama'] = 'true';
    
    // Call the utility function
    const useOllama = getUseOllama();
    
    // Check if it returns the correct value
    expect(useOllama).toBe(true);
  });
});
