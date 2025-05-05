import { useState, useEffect } from 'react';

// API key storage key
const API_KEY_STORAGE_KEY = 'groq_api_key';
const USE_OLLAMA_STORAGE_KEY = 'use_ollama';

// Function to get API key from sessionStorage (temporary storage)
export const getApiKey = (): string | null => {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(API_KEY_STORAGE_KEY);
};

// Function to get useOllama setting from localStorage
// We keep this in localStorage as it's not sensitive
export const getUseOllama = (): boolean => {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem(USE_OLLAMA_STORAGE_KEY) === 'true';
};

// Function to save API key to sessionStorage (temporary storage)
export const saveApiKey = (apiKey: string | null): void => {
  if (typeof window === 'undefined') return;
  if (apiKey) {
    sessionStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
  } else {
    sessionStorage.removeItem(API_KEY_STORAGE_KEY);
  }
};

// Function to save useOllama setting to localStorage
export const saveUseOllama = (useOllama: boolean): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USE_OLLAMA_STORAGE_KEY, useOllama ? 'true' : 'false');
};

// Custom hook to manage API key
export const useApiKey = () => {
  const [apiKey, setApiKeyState] = useState<string | null>(null);
  const [useOllama, setUseOllamaState] = useState<boolean>(false);

  // Load API key and Ollama setting on mount
  useEffect(() => {
    setApiKeyState(getApiKey());
    setUseOllamaState(getUseOllama());
  }, []);

  // Function to update API key
  const setApiKey = (newApiKey: string | null) => {
    saveApiKey(newApiKey);
    setApiKeyState(newApiKey);
  };

  // Function to update useOllama
  const setUseOllama = (newUseOllama: boolean) => {
    saveUseOllama(newUseOllama);
    setUseOllamaState(newUseOllama);
  };

  return { apiKey, setApiKey, useOllama, setUseOllama };
};

export default useApiKey;
