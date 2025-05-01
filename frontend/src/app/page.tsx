// frontend/src/app/page.tsx
"use client";

import React, { useState, useEffect, useCallback } from "react";
import ReactECharts from "echarts-for-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Terminal, Settings } from "lucide-react";
import { ApiKeySettings, getApiKey, getUseOllama } from "@/components/ApiKeySettings";
import { AgentConversationMonitor } from "@/components/AgentConversationMonitor";

interface AdminLog {
  timestamp: string;
  // Logs now contain separate model IDs
  analyst_model?: string;
  coder_model?: string;
  messages: Array<{
    name: string | null; // Role can sometimes be null in groupchat messages
    content: string;
    role: string; // Agent name is in 'role' for groupchat messages
  }>;
}

// Type for ECharts configurations
type EChartsConfig = Record<string, any>;


// Backend API URL (adjust if your backend runs elsewhere)
const API_BASE_URL = "http://localhost:5001/api"; // Backend runs on port 5001

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  // Update state types to use the generic VegaSpec
  const [visualizations, setVisualizations] = useState<EChartsConfig[]>([]);
  const [promptedVisualizations, setPromptedVisualizations] = useState<EChartsConfig[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingPrompted, setIsLoadingPrompted] = useState(false);
  const [adminLogs, setAdminLogs] = useState<AdminLog[]>([]);
  const [showAdminMonitor, setShowAdminMonitor] = useState(true);
  const [showApiSettings, setShowApiSettings] = useState(false);
  // API key and Ollama state
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [useOllama, setUseOllama] = useState<boolean>(false);
  // Separate state for analyst and coder models
  const [selectedAnalystModel, setSelectedAnalystModel] = useState<string>('llama3-70b-8192');
  const [selectedCoderModel, setSelectedCoderModel] = useState<string>('llama3-70b-8192');
  const [availableModels, setAvailableModels] = useState<{[key: string]: string}>({});
  const [promptText, setPromptText] = useState('');

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
      setVisualizations([]); // Clear previous results
      setPromptedVisualizations([]); // Clear prompted results too
      setError(null);
    }
  }, []);

  // Fetch admin logs periodically or on demand
  const fetchAdminLogs = useCallback(() => {
    // Skip if no API key is available and not using Ollama
    if (!apiKey && !useOllama) return;

    // Prepare headers
    const headers: Record<string, string> = {};

    if (apiKey) {
      headers['X-API-KEY'] = apiKey;
    }

    if (useOllama) {
      headers['USE-OLLAMA'] = 'true';
    }

    fetch(`${API_BASE_URL}/admin/logs`, {
      headers
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        // Ensure logs is an array
        setAdminLogs(Array.isArray(data.logs) ? data.logs.reverse() : []); // Show newest first
        setAvailableModels(data.available_models || {});
      })
      .catch(error => console.error('Error fetching admin logs:', error));
  }, [apiKey, useOllama]);


  // Load API key and Ollama setting on component mount
  useEffect(() => {
    const savedApiKey = getApiKey();
    const savedUseOllama = getUseOllama();

    setApiKey(savedApiKey);
    setUseOllama(savedUseOllama);

    // If no API key is found and not using Ollama, show the API settings
    if (!savedApiKey && !savedUseOllama) {
      setShowApiSettings(true);
    }
  }, []);

  useEffect(() => {
    fetchAdminLogs(); // Fetch initial logs
    // Optional: Fetch logs periodically
    // const intervalId = setInterval(fetchAdminLogs, 10000); // Fetch every 10 seconds
    // return () => clearInterval(intervalId); // Cleanup interval on unmount
  }, [fetchAdminLogs]);

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a CSV file first.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setVisualizations([]); // Clear previous visualizations

    // Upload the file
    const formData = new FormData();
    formData.append('file', file);

    // Check if API key is available or Ollama is enabled
    if (!apiKey && !useOllama) {
      setError("Either an API key or Ollama is required. Please configure your settings.");
      setShowApiSettings(true);
      setIsLoading(false);
      return;
    }

    try {
      // Prepare headers
      const headers: Record<string, string> = {};

      if (apiKey) {
        headers['X-API-KEY'] = apiKey;
      }

      if (useOllama) {
        headers['USE-OLLAMA'] = 'true';
      }

      const uploadResponse = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        headers,
        body: formData
      });

      const uploadData = await uploadResponse.json();

      if (!uploadResponse.ok || uploadData.error) {
        throw new Error(uploadData.error || `File upload failed with status: ${uploadResponse.status}`);
      }

      // Fetch initial visualizations with selected models
      const vizResponse = await fetch(`${API_BASE_URL}/visualizations?analyst_model=${selectedAnalystModel}&coder_model=${selectedCoderModel}`, {
        headers
      });
      const vizData = await vizResponse.json();

      if (!vizResponse.ok || vizData.error) {
        throw new Error(vizData.error || `Fetching visualizations failed with status: ${vizResponse.status}`);
      }

      setVisualizations(vizData.visualizations || []);
      fetchAdminLogs(); // Refresh logs after successful operation

    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during upload/analysis.');
      console.error('Error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to handle cancellation of initial analysis
  const handleCancelUpload = () => {
      setIsLoading(false); // Reset loading state
      setError("Analysis cancelled by user."); // Provide feedback
      // Note: This doesn't stop the backend process, only resets frontend state
  };

  const handlePrompt = async () => {
    // Allow prompt even without file upload if backend handles default dataset
    if (!promptText.trim()) {
      setError("Please enter a prompt.");
      return;
    }

    setIsLoadingPrompted(true);
    setError(null);
    setPromptedVisualizations([]); // Clear previous prompted visualizations

    // Check if API key is available or Ollama is enabled
    if (!apiKey && !useOllama) {
      setError("Either an API key or Ollama is required. Please configure your settings.");
      setShowApiSettings(true);
      setIsLoadingPrompted(false);
      return;
    }

    try {
      // Prepare headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      if (apiKey) {
        headers['X-API-KEY'] = apiKey;
      }

      if (useOllama) {
        headers['USE-OLLAMA'] = 'true';
      }

      const response = await fetch(`${API_BASE_URL}/visualizations/prompt`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          prompt: promptText,
          analyst_model_id: selectedAnalystModel, // Pass analyst model
          coder_model_id: selectedCoderModel    // Pass coder model
        })
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        throw new Error(data.error || `Generating prompted visualization failed with status: ${response.status}`);
      }

      setPromptedVisualizations(data.visualizations || []);
      fetchAdminLogs(); // Refresh logs after successful operation

    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred generating the prompted visualization.');
      console.error('Error:', err);
    } finally {
      setIsLoadingPrompted(false);
    }
  };

   // Function to handle cancellation of prompted generation
   const handleCancelPrompt = () => {
      setIsLoadingPrompted(false); // Reset loading state
      setError("Generation cancelled by user."); // Provide feedback
      // Note: This doesn't stop the backend process, only resets frontend state
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-6 md:p-12 lg:p-24 bg-gray-50">
      <div className="z-10 w-full max-w-7xl items-center justify-between font-mono text-sm lg:flex mb-8">
        <h1 className="text-2xl font-bold text-center lg:text-left">Agentic Data Visualization</h1>
      </div>

      {/* Main content area with two columns */}
      <div className="w-full max-w-7xl flex flex-col lg:flex-row gap-6">
        {/* Left column - Steps and Visualizations */}
        <div className="flex-1 flex flex-col gap-6">
          {/* Step 1: API Key Settings */}
          <Card className="w-full">
            <CardHeader>
              <CardTitle>1. Configure API Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ApiKeySettings
                onApiKeySaved={(newApiKey, newUseOllama) => {
                  setApiKey(newApiKey);
                  setUseOllama(newUseOllama);
                  fetchAdminLogs(); // Refresh data with new settings
                }}
              />
            </CardContent>
          </Card>

          {/* Step 2: File Upload & Model Selection */}
          <Card className="w-full">
            <CardHeader>
              <CardTitle>2. Upload & Analyze Data</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* File Input */}
              <div className="grid w-full items-center gap-1.5">
                <Label htmlFor="csv-file">CSV File (Optional if using default)</Label>
                <Input id="csv-file" type="file" accept=".csv" onChange={handleFileChange} />
              </div>

              {/* Model Selectors */}
              <div className="flex flex-wrap gap-4 items-end">
                {/* Analyst Model Selector */}
                <div className="flex flex-col">
                  <Label htmlFor="analyst-model-select" className="text-xs mb-1">Analyst Model</Label>
                  <select
                    id="analyst-model-select"
                    value={selectedAnalystModel}
                    onChange={(e) => setSelectedAnalystModel(e.target.value)}
                    className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
                  >
                    {Object.entries(availableModels).map(([id, name]) => (
                      <option key={id} value={id}>{name}</option>
                    ))}
                  </select>
                </div>
                {/* Coder Model Selector */}
                <div className="flex flex-col">
                  <Label htmlFor="coder-model-select" className="text-xs mb-1">Coder Model</Label>
                  <select
                    id="coder-model-select"
                    value={selectedCoderModel}
                    onChange={(e) => setSelectedCoderModel(e.target.value)}
                    className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
                  >
                    {Object.entries(availableModels).map(([id, name]) => (
                      <option key={id} value={id}>{name}</option>
                    ))}
                  </select>
                </div>
                {/* Upload/Cancel Button */}
                {!isLoading ? (
                  <button
                    onClick={handleUpload}
                    disabled={!file} // Disable only if no file selected
                    title={!file ? "Select a file to upload" : "Upload file and get initial suggestions"}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Upload & Analyze
                  </button>
                ) : (
                  <button
                    onClick={handleCancelUpload}
                    title="Cancel analysis"
                    className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
                  >
                    Cancel
                  </button>
                )}
              </div>

              {/* Error Display */}
              {error && (
                <Alert variant="destructive">
                  <Terminal className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Step 3: Request Specific Visualization */}
          <Card className="w-full">
            <CardHeader>
              <CardTitle>3. Request Specific Visualization</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="prompt-input">Enter your visualization request</Label>
                <div className="flex gap-2">
                  <Input
                    id="prompt-input"
                    type="text"
                    placeholder="e.g., Show total commitment per province"
                    value={promptText}
                    onChange={(e) => setPromptText(e.target.value)}
                    className="flex-grow"
                  />
                  {!isLoadingPrompted ? (
                    <button
                      onClick={handlePrompt}
                      disabled={!promptText.trim()}
                      title={!promptText.trim() ? "Enter a prompt first" : "Generate visualization from prompt"}
                      className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Generate
                    </button>
                  ) : (
                    <button
                      onClick={handleCancelPrompt}
                      title="Cancel generation"
                      className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Initial Visualizations Dashboard */}
          {(isLoading || visualizations.length > 0) && (
            <Card className="w-full">
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-xl font-bold">Initial Financial Analysis</CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {isLoading && (
                  <div className="flex justify-center items-center h-60">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
                  </div>
                )}
                {!isLoading && visualizations.length === 0 && (
                  <div className="text-center py-10 text-gray-500">
                    <p>No visualizations generated yet. Upload a CSV file to start analysis.</p>
                  </div>
                )}
                {visualizations.length > 0 && (
                  <div className="grid grid-cols-1 gap-8">
                    {/* First row - full width for important visualizations */}
                    {visualizations.length > 0 && (
                      <div className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                        <ReactECharts
                          option={visualizations[0]}
                          style={{ height: 450, width: '100%' }}
                          opts={{ renderer: 'canvas' }}
                        />
                      </div>
                    )}

                    {/* Second row - two columns for additional visualizations */}
                    {visualizations.length > 1 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {visualizations.slice(1).map((config: EChartsConfig, index: number) => (
                          <div key={`initial-${index+1}`} className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                            <ReactECharts
                              option={config}
                              style={{ height: 400, width: '100%' }}
                              opts={{ renderer: 'canvas' }}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Prompted Visualizations Dashboard */}
          {(isLoadingPrompted || promptedVisualizations.length > 0) && (
            <Card className="w-full">
              <CardHeader className="border-b pb-3">
                <CardTitle className="text-xl font-bold">Custom Visualization</CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {isLoadingPrompted && (
                  <div className="flex justify-center items-center h-60">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-700"></div>
                  </div>
                )}
                {!isLoadingPrompted && promptedVisualizations.length === 0 && (
                  <div className="text-center py-10 text-gray-500">
                    <p>No custom visualizations generated yet. Enter a specific request.</p>
                  </div>
                )}
                {promptedVisualizations.length > 0 && (
                  <div className="grid grid-cols-1 gap-8">
                    {/* First prompted visualization - full width */}
                    {promptedVisualizations.length > 0 && (
                      <div className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                        <ReactECharts
                          option={promptedVisualizations[0]}
                          style={{ height: 450, width: '100%' }}
                          opts={{ renderer: 'canvas' }}
                        />
                      </div>
                    )}

                    {/* Additional prompted visualizations - two columns */}
                    {promptedVisualizations.length > 1 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {promptedVisualizations.slice(1).map((config: EChartsConfig, index: number) => (
                          <div key={`prompted-${index+1}`} className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                            <ReactECharts
                              option={config}
                              style={{ height: 400, width: '100%' }}
                              opts={{ renderer: 'canvas' }}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right column - Agent Monitor */}
        <div className="lg:w-1/3 w-full">
          <div className="sticky top-6">
            <Card className="w-full">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Agent Monitor</CardTitle>
                <button
                  onClick={() => setShowAdminMonitor(!showAdminMonitor)}
                  className="text-sm text-gray-600 hover:text-gray-800"
                >
                  {showAdminMonitor ? 'Hide' : 'Show'}
                </button>
              </CardHeader>
              <CardContent>
                {showAdminMonitor ? (
                  <AgentConversationMonitor logs={adminLogs} />
                ) : (
                  <div className="text-center py-10 text-gray-500">
                    <p>Agent monitor is hidden. Click "Show" to view agent conversations.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </main>
  );
}
