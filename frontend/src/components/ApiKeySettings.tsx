import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Save, Server, Check, Loader2 } from 'lucide-react';
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";

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
  const [availableModels, setAvailableModels] = useState<Record<string, string>>({});
  const [showModels, setShowModels] = useState<boolean>(false);

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
    setShowModels(false);
    setAvailableModels({});

    try {
      const headers: Record<string, string> = {};

      // Always set the USE-OLLAMA header, either true or false
      // This ensures we explicitly communicate the user's choice to the backend
      headers['USE-OLLAMA'] = useOllamaFlag ? 'true' : 'false';

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
      console.log("API key validation response:", data);

      if (!response.ok) {
        setValidationError(data.message || 'API key validation failed');
        return false;
      }

      // Store the available models
      if (data.available_models) {
        const modelCount = Object.keys(data.available_models).length;
        console.log(`Found ${modelCount} available models`);
        setAvailableModels(data.available_models);
        setShowModels(true);
      } else {
        console.warn("No models found in the response");
        setValidationError("API key validated but no models were found. Please try again.");
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

    setIsValidating(true);

    try {
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

        setAvailableModels({});
        setShowModels(false);

        // Notify parent component about the API key change
        onApiKeySaved(apiKey, useOllama);
      }
    } catch (error) {
      console.error("Error saving API key:", error);
      setValidationError('Failed to save API key. Please try again.');
    } finally {
      setIsValidating(false);
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
          {/* Model Provider Selection */}
          <div className="space-y-4 mb-6">
            <Label className="text-base font-medium">Select Model Provider</Label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Groq Card */}
              <div
                className={`border rounded-lg p-4 cursor-pointer transition-all ${!useOllama ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}
                onClick={() => {
                  setUseOllama(false);
                  setIsSaved(false);
                }}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Groq Cloud API</h3>
                  <div className={`w-4 h-4 rounded-full ${!useOllama ? 'bg-blue-500' : 'border border-gray-300'}`}></div>
                </div>
                <p className="text-sm text-gray-500">Use Groq's cloud-hosted models (requires API key)</p>
              </div>

              {/* Ollama Card */}
              <div
                className={`border rounded-lg p-4 cursor-pointer transition-all ${useOllama ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}
                onClick={() => {
                  setUseOllama(true);
                  setIsSaved(false);
                }}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Local Ollama</h3>
                  <div className={`w-4 h-4 rounded-full ${useOllama ? 'bg-blue-500' : 'border border-gray-300'}`}></div>
                </div>
                <p className="text-sm text-gray-500">Use models running on your local Ollama server</p>
              </div>
            </div>
          </div>

          {/* Groq API Key Input - shown only if Groq is selected */}
          {!useOllama && (
            <div className="space-y-2 border-t pt-4">
              <Label htmlFor="api-key">Groq API Key</Label>
              <div className="flex">
                <Input
                  id="api-key"
                  type={showApiKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => {
                    setApiKey(e.target.value);
                    setIsSaved(false);
                  }}
                  placeholder="Enter your Groq API key"
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
              <p className="text-xs text-gray-500 mt-1">
                Get your API key from <a href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">Groq Console</a>
              </p>
            </div>
          )}

          {/* Ollama Settings - shown only if Ollama is selected */}
          {useOllama && (
            <div className="space-y-2 border-t pt-4">
              <Label htmlFor="ollama-status" className="text-base">Ollama Status</Label>
              <div className="flex items-center space-x-2 bg-gray-50 p-3 rounded-md">
                <Server className="h-5 w-5 text-green-500" />
                <span className="text-sm">Using local Ollama models at <code className="bg-gray-100 px-1 py-0.5 rounded">http://localhost:11434</code></span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Make sure Ollama is running and has models installed. Run <code className="bg-gray-100 px-1 py-0.5 rounded">ollama list</code> to see available models.
              </p>
            </div>
          )}

          {/* Status Messages */}
          {isSaved && !validationError && (
            <div className="space-y-2">
              <p className="text-sm text-green-600 flex items-center">
                <Check className="h-4 w-4 mr-1" />
                {useOllama
                  ? "Ollama configuration saved"
                  : "API key saved and validated"}
              </p>

              {/* Available Models Section */}
              {showModels && Object.keys(availableModels).length > 0 && (
                <div className="mt-4">
                  <div className="flex justify-between items-center mb-2">
                    <Label className="text-sm font-medium">Available Models</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowModels(!showModels)}
                      className="h-6 px-2 text-xs"
                    >
                      {showModels ? 'Hide' : 'Show'}
                    </Button>
                  </div>

                  <div className="bg-gray-50 p-3 rounded-md border border-gray-200 max-h-40 overflow-y-auto">
                    <div className="grid grid-cols-1 gap-1">
                      {Object.entries(availableModels || {}).map(([id, name]) => (
                        <div key={id} className="text-xs flex items-center py-1 px-2 rounded hover:bg-gray-100">
                          <span className="font-mono text-gray-500 mr-2">{id.startsWith('ollama:') ? '🖥️' : '☁️'}</span>
                          <span className="flex-grow">{name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {validationError && (
            <Alert variant="destructive" className="mt-2">
              <AlertDescription className="text-sm">{validationError}</AlertDescription>
            </Alert>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          onClick={handleSaveApiKey}
          disabled={(!apiKey.trim() && !useOllama) || isValidating || (isSaved && !validationError)}
          className="flex items-center"
          variant={isSaved && !validationError ? "outline" : "default"}
        >
          {isValidating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Validating...
            </>
          ) : (
            <>
              {isSaved && !validationError ? (
                <Check className="mr-2 h-4 w-4" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              {isSaved && !validationError ? 'Settings Saved' : 'Save Settings'}
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
