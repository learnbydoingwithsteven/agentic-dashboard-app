import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Save, Server } from 'lucide-react';
import { Switch } from "@/components/ui/switch";

// Local storage keys
const API_KEY_STORAGE_KEY = 'groq_api_key';
const USE_OLLAMA_STORAGE_KEY = 'use_ollama';

interface ApiKeySettingsProps {
  onApiKeySaved: (apiKey: string, useOllama: boolean) => void;
}

export function ApiKeySettings({ onApiKeySaved }: ApiKeySettingsProps) {
  const [apiKey, setApiKey] = useState<string>('');
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  const [isSaved, setIsSaved] = useState<boolean>(false);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [useOllama, setUseOllama] = useState<boolean>(false);

  // Load settings from localStorage on component mount
  useEffect(() => {
    const savedApiKey = localStorage.getItem(API_KEY_STORAGE_KEY);
    const savedUseOllama = localStorage.getItem(USE_OLLAMA_STORAGE_KEY) === 'true';

    if (savedApiKey) {
      setApiKey(savedApiKey);
      setIsSaved(true);
    }

    setUseOllama(savedUseOllama);
  }, []);

  const validateApiKey = async (key: string, useOllamaFlag: boolean): Promise<boolean> => {
    setIsValidating(true);
    setValidationError(null);

    try {
      const headers: Record<string, string> = {};

      // If using Ollama, set the USE-OLLAMA header
      if (useOllamaFlag) {
        headers['USE-OLLAMA'] = 'true';
      }

      // If we have an API key, include it
      if (key.trim()) {
        headers['X-API-KEY'] = key;
      } else if (!useOllamaFlag) {
        // If not using Ollama and no API key, fail validation
        setValidationError('API key is required unless using Ollama');
        return false;
      }

      const response = await fetch('http://localhost:5001/api/check_api_key', {
        method: 'GET',
        headers
      });

      const data = await response.json();

      if (!response.ok) {
        setValidationError(data.message || 'API key validation failed');
        return false;
      }

      return true;
    } catch (error) {
      setValidationError('Failed to validate API key. Please check your connection.');
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const handleSaveApiKey = async () => {
    // If not using Ollama, require an API key
    if (!useOllama && !apiKey.trim()) {
      setValidationError('API key is required unless using Ollama');
      return;
    }

    const isValid = await validateApiKey(apiKey, useOllama);

    if (isValid) {
      // Save API key if provided
      if (apiKey.trim()) {
        localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
      }

      // Save Ollama setting
      localStorage.setItem(USE_OLLAMA_STORAGE_KEY, useOllama.toString());

      setIsSaved(true);
      setValidationError(null);
      onApiKeySaved(apiKey, useOllama);
    }
  };

  const toggleShowApiKey = () => {
    setShowApiKey(!showApiKey);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Model Settings</CardTitle>
        <CardDescription>
          Choose between using Groq API or local Ollama models for visualization generation.
          {!apiKey && !useOllama && (
            <span className="text-red-500 block mt-1">
              Either a Groq API key or Ollama is required for this application to work.
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Ollama Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="use-ollama" className="text-base">Use Local Ollama Models</Label>
              <p className="text-sm text-muted-foreground">
                Use models running on your local Ollama server
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="use-ollama"
                checked={useOllama}
                onCheckedChange={(checked) => {
                  setUseOllama(checked);
                  setIsSaved(false);
                }}
              />
              <Server className={`h-4 w-4 ${useOllama ? 'text-green-500' : 'text-gray-400'}`} />
            </div>
          </div>

          {/* API Key Input - shown if not using Ollama or if using both */}
          <div className={`space-y-2 ${useOllama ? 'opacity-50' : ''}`}>
            <Label htmlFor="api-key">Groq API Key {useOllama && '(Optional)'}</Label>
            <div className="flex">
              <Input
                id="api-key"
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  setIsSaved(false);
                }}
                placeholder={useOllama ? "Optional when using Ollama" : "Enter your Groq API key"}
                className="flex-grow"
                disabled={isValidating}
              />
              <Button
                variant="outline"
                size="icon"
                onClick={toggleShowApiKey}
                className="ml-2"
                title={showApiKey ? "Hide API key" : "Show API key"}
                disabled={isValidating}
              >
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          {/* Status Messages */}
          {isSaved && !validationError && (
            <p className="text-sm text-green-600">
              {useOllama
                ? "Ollama configuration saved"
                : "API key saved and validated"}
            </p>
          )}
          {validationError && (
            <p className="text-sm text-red-600">{validationError}</p>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          onClick={handleSaveApiKey}
          disabled={(!apiKey.trim() && !useOllama) || isValidating || (isSaved && !validationError)}
          className="flex items-center"
        >
          {isValidating ? (
            <>
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"></div>
              Validating...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              {isSaved ? 'Update Settings' : 'Save Settings'}
            </>
          )}
        </Button>

        {isSaved && validationError && (
          <p className="text-sm text-amber-600">Your configuration may be invalid. Please update it.</p>
        )}
      </CardFooter>
    </Card>
  );
}

// Export utility functions to get the API key and Ollama setting
export function getApiKey(): string | null {
  return localStorage.getItem(API_KEY_STORAGE_KEY);
}

export function getUseOllama(): boolean {
  return localStorage.getItem(USE_OLLAMA_STORAGE_KEY) === 'true';
}
