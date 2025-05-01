// frontend/src/app/page.tsx
"use client";

import React, { useState, useEffect, useCallback } from "react";
import ReactECharts from "echarts-for-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Terminal, Settings, Code } from "lucide-react";
import { ApiKeySettings, getApiKey, getUseOllama } from "@/components/ApiKeySettings";
import { AgentConversationMonitor } from "@/components/AgentConversationMonitor";
import { DebugVisualization } from "@/components/DebugVisualization";
import { CodeVisualization } from "@/components/CodeVisualization";

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

// Define the type for Plotly visualization
interface PlotlyVisualization {
  figure: any;
  code: string;
  output?: string;
  error?: string;
}


// Backend API URL (adjust if your backend runs elsewhere)
const API_BASE_URL = "http://localhost:5001/api"; // Backend runs on port 5001

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  // Update state types to use the generic VegaSpec
  const [visualizations, setVisualizations] = useState<EChartsConfig[]>([]);
  const [promptedVisualizations, setPromptedVisualizations] = useState<EChartsConfig[]>([]);

  // Plotly visualizations state
  const [plotlyVisualizations, setPlotlyVisualizations] = useState<PlotlyVisualization[]>([]);
  const [promptedPlotlyVisualizations, setPromptedPlotlyVisualizations] = useState<PlotlyVisualization[]>([]);
  const [isExecutingCode, setIsExecutingCode] = useState<boolean>(false);
  const [executingIndex, setExecutingIndex] = useState<number>(-1);

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingPrompted, setIsLoadingPrompted] = useState(false);
  const [adminLogs, setAdminLogs] = useState<AdminLog[]>([]);
  const [showAdminMonitor, setShowAdminMonitor] = useState(true);
  const [showApiSettings, setShowApiSettings] = useState(false);
  // API key and Ollama state
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [useOllama, setUseOllama] = useState<boolean>(false);
  // Separate state for all agent models
  const [selectedAnalystModel, setSelectedAnalystModel] = useState<string>('llama3-70b-8192');
  const [selectedCoderModel, setSelectedCoderModel] = useState<string>('llama3-70b-8192');
  const [selectedManagerModel, setSelectedManagerModel] = useState<string>('llama3-70b-8192');
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

  // Prepare headers for API requests
  const getRequestHeaders = useCallback((contentType?: string): Record<string, string> => {
    const headers: Record<string, string> = {};

    // Add content type if provided
    if (contentType) {
      headers['Content-Type'] = contentType;
    }

    // Add API key if available
    if (apiKey) {
      headers['X-API-KEY'] = apiKey;
    }

    // Always add USE-OLLAMA header with explicit true/false value
    headers['USE-OLLAMA'] = useOllama ? 'true' : 'false';

    return headers;
  }, [apiKey, useOllama]);

  // State to track if there are new logs
  const [hasNewLogs, setHasNewLogs] = useState(false);

  // Fetch admin logs periodically or on demand
  const fetchAdminLogs = useCallback(() => {
    // Skip if no API key is available and not using Ollama
    if (!apiKey && !useOllama) return;

    // Track the current log count to detect new logs
    const currentLogCount = adminLogs.length;

    fetch(`${API_BASE_URL}/admin/logs`, {
      headers: getRequestHeaders()
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        // Ensure logs is an array
        const newLogs = Array.isArray(data.logs) ? data.logs.reverse() : []; // Show newest first

        // Check if we have new logs
        if (newLogs.length > currentLogCount) {
          console.log(`New logs detected: ${newLogs.length - currentLogCount} new entries`);
          setHasNewLogs(true);

          // If the agent monitor is visible, update logs immediately
          if (showAdminMonitor) {
            setAdminLogs(newLogs);
          }
        } else if (showAdminMonitor) {
          // If monitor is visible, always update logs even if no new ones
          setAdminLogs(newLogs);
        }

        // Always update available models
        setAvailableModels(data.available_models || {});
      })
      .catch(error => console.error('Error fetching admin logs:', error));
  }, [apiKey, useOllama, getRequestHeaders, adminLogs.length, showAdminMonitor]);


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

    // Set up polling for real-time log updates
    const intervalId = setInterval(fetchAdminLogs, 3000); // Fetch every 3 seconds

    // Cleanup interval on unmount
    return () => clearInterval(intervalId);
  }, [fetchAdminLogs]);

  const handleUpload = useCallback(async () => {
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
      // Get headers for the request
      const headers = getRequestHeaders();

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
      const vizResponse = await fetch(`${API_BASE_URL}/visualizations?analyst_model=${selectedAnalystModel}&coder_model=${selectedCoderModel}&manager_model=${selectedManagerModel}`, {
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
  }, [file, apiKey, useOllama, selectedAnalystModel, selectedCoderModel, selectedManagerModel, getRequestHeaders, fetchAdminLogs]);

  // Function to handle cancellation of initial analysis
  const handleCancelUpload = async () => {
    try {
      // Call the backend to cancel the job
      const response = await fetch(`${API_BASE_URL}/cancel`, {
        method: 'POST',
        headers: getRequestHeaders('application/json'),
        body: JSON.stringify({})
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `Cancellation failed with status: ${response.status}`);
      }

      // Reset frontend state
      setIsLoading(false);
      setError("Analysis cancelled by user. The agent will stop at the next opportunity.");

      // Refresh logs to show cancellation
      setTimeout(fetchAdminLogs, 1000);

    } catch (err: any) {
      console.error('Error cancelling job:', err);
      setIsLoading(false);
      setError(`Failed to cancel job: ${err.message}`);
    }
  };

  const handlePrompt = useCallback(async () => {
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
      // Get headers for the request with content type
      const headers = getRequestHeaders('application/json');

      const response = await fetch(`${API_BASE_URL}/visualizations/prompt`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          prompt: promptText,
          analyst_model_id: selectedAnalystModel, // Pass analyst model
          coder_model_id: selectedCoderModel,    // Pass coder model
          manager_model_id: selectedManagerModel  // Pass manager model
        })
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        throw new Error(data.error || `Generating prompted visualization failed with status: ${response.status}`);
      }

      // Check if we have Plotly visualizations
      if (data.code_blocks && Array.isArray(data.code_blocks)) {
        // We have Plotly visualizations
        const plotlyViz = data.visualizations.map((figure: any, index: number) => ({
          figure,
          code: data.code_blocks[index] || '',
          output: data.outputs && data.outputs[index] ? data.outputs[index] : '',
          error: data.errors && data.errors[index] ? data.errors[index] : ''
        }));
        setPromptedPlotlyVisualizations(plotlyViz);
      } else {
        // We have ECharts visualizations (legacy)
        setPromptedVisualizations(data.visualizations || []);
      }

      fetchAdminLogs(); // Refresh logs after successful operation

    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred generating the prompted visualization.');
      console.error('Error:', err);
    } finally {
      setIsLoadingPrompted(false);
    }
  }, [promptText, apiKey, useOllama, selectedAnalystModel, selectedCoderModel, selectedManagerModel, getRequestHeaders, fetchAdminLogs]);

  // Function to handle cancellation of prompted generation
  const handleCancelPrompt = async () => {
    try {
      // Call the backend to cancel the job
      const response = await fetch(`${API_BASE_URL}/cancel`, {
        method: 'POST',
        headers: getRequestHeaders('application/json'),
        body: JSON.stringify({})
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `Cancellation failed with status: ${response.status}`);
      }

      // Reset frontend state
      setIsLoadingPrompted(false);
      setError("Generation cancelled by user. The agent will stop at the next opportunity.");

      // Refresh logs to show cancellation
      setTimeout(fetchAdminLogs, 1000);

    } catch (err: any) {
      console.error('Error cancelling job:', err);
      setIsLoadingPrompted(false);
      setError(`Failed to cancel job: ${err.message}`);
    }
  };

  // Function to reset the backend
  const handleResetBackend = async () => {
    if (!confirm("Are you sure you want to reset the backend? This will clear all logs and current jobs.")) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/reset`, {
        method: 'POST',
        headers: getRequestHeaders('application/json'),
      });

      const data = await response.json();

      if (response.ok) {
        // Clear visualizations
        setVisualizations([]);
        setPromptedVisualizations([]);
        setPlotlyVisualizations([]);
        setPromptedPlotlyVisualizations([]);

        // Reset loading states
        setIsLoading(false);
        setIsLoadingPrompted(false);
        setIsExecutingCode(false);

        // Clear error message
        setError(null);

        // Refresh logs
        setAdminLogs([]);
        fetchAdminLogs();

        // Show success message
        setError("Backend state has been reset successfully.");
      } else {
        setError(data.message || "Failed to reset backend");
      }
    } catch (err: any) {
      console.error('Error resetting backend:', err);
      setError(`Error resetting backend: ${err.message}`);
    }
  };

  // Function to execute Python code
  const handleExecuteCode = async (code: string, index: number) => {
    setIsExecutingCode(true);
    setExecutingIndex(index);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/execute_code`, {
        method: 'POST',
        headers: getRequestHeaders('application/json'),
        body: JSON.stringify({ code })
      });

      const data = await response.json();

      if (response.ok) {
        // Update the visualization at the specified index
        if (index >= 0) {
          // Check if this is a prompted visualization or a regular one
          if (index < plotlyVisualizations.length) {
            const updatedVisualizations = [...plotlyVisualizations];
            updatedVisualizations[index] = {
              figure: data.figure,
              code: data.code,
              output: data.output,
              error: data.error
            };
            setPlotlyVisualizations(updatedVisualizations);
          } else {
            // It's a prompted visualization
            const promptedIndex = index - plotlyVisualizations.length;
            if (promptedIndex >= 0 && promptedIndex < promptedPlotlyVisualizations.length) {
              const updatedVisualizations = [...promptedPlotlyVisualizations];
              updatedVisualizations[promptedIndex] = {
                figure: data.figure,
                code: data.code,
                output: data.output,
                error: data.error
              };
              setPromptedPlotlyVisualizations(updatedVisualizations);
            }
          }
        } else {
          // Add as a new visualization
          setPlotlyVisualizations([
            ...plotlyVisualizations,
            {
              figure: data.figure,
              code: data.code,
              output: data.output,
              error: data.error
            }
          ]);
        }
      } else {
        setError(data.message || data.error || "Failed to execute code");
      }
    } catch (err: any) {
      console.error('Error executing code:', err);
      setError(`Error executing code: ${err.message}`);
    } finally {
      setIsExecutingCode(false);
      setExecutingIndex(-1);
    }
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

                  // Force a direct fetch of available models with the new API key
                  const headers: Record<string, string> = {};
                  if (newApiKey) {
                    headers['X-API-KEY'] = newApiKey;
                  }
                  // Always set USE-OLLAMA header with explicit true/false value
                  headers['USE-OLLAMA'] = newUseOllama ? 'true' : 'false';

                  console.log("Main component: Refreshing models with new API key...");
                  fetch(`${API_BASE_URL}/check_api_key`, {
                    method: 'GET',
                    headers
                  })
                    .then(response => {
                      console.log("API key validation status:", response.status);
                      return response.json();
                    })
                    .then(data => {
                      console.log("API key validation response:", data);

                      if (data.available_models && Object.keys(data.available_models).length > 0) {
                        console.log("Main component: Models updated successfully:", Object.keys(data.available_models).length);
                        setAvailableModels(data.available_models);

                        // Set default models based on what's available
                        const firstModel = Object.keys(data.available_models)[0];
                        console.log("Setting default model to:", firstModel);
                        setSelectedAnalystModel(firstModel);
                        setSelectedCoderModel(firstModel);
                        setSelectedManagerModel(firstModel);
                      } else {
                        console.warn("No models found in the response or empty models object");
                        // Try fetching admin logs as a fallback to get models
                        fetchAdminLogs();
                      }
                    })
                    .catch(error => {
                      console.error("Error fetching models:", error);
                      // Try fetching admin logs as a fallback
                      fetchAdminLogs();
                    });

                  // Also refresh admin logs to get the latest data
                  fetchAdminLogs();
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
                    {/* Group models by provider */}
                    {useOllama ? (
                      // Show only Ollama models when Ollama is selected
                      <>
                        <optgroup label="Ollama Models">
                          {Object.entries(availableModels)
                            .filter(([id]) => id.startsWith('ollama:'))
                            .map(([id, name]) => (
                              <option key={id} value={id}>{name}</option>
                            ))}
                        </optgroup>
                      </>
                    ) : (
                      // Show only Groq models when Groq is selected
                      <>
                        <optgroup label="Groq Models">
                          {Object.entries(availableModels)
                            .filter(([id]) => !id.startsWith('ollama:'))
                            .map(([id, name]) => (
                              <option key={id} value={id}>{name}</option>
                            ))}
                        </optgroup>
                      </>
                    )}
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
                    {/* Group models by provider */}
                    {useOllama ? (
                      // Show only Ollama models when Ollama is selected
                      <>
                        <optgroup label="Ollama Models">
                          {Object.entries(availableModels)
                            .filter(([id]) => id.startsWith('ollama:'))
                            .map(([id, name]) => (
                              <option key={id} value={id}>{name}</option>
                            ))}
                        </optgroup>
                      </>
                    ) : (
                      // Show only Groq models when Groq is selected
                      <>
                        <optgroup label="Groq Models">
                          {Object.entries(availableModels)
                            .filter(([id]) => !id.startsWith('ollama:'))
                            .map(([id, name]) => (
                              <option key={id} value={id}>{name}</option>
                            ))}
                        </optgroup>
                      </>
                    )}
                  </select>
                </div>
                {/* Manager Model Selector */}
                <div className="flex flex-col">
                  <Label htmlFor="manager-model-select" className="text-xs mb-1">Manager Model</Label>
                  <select
                    id="manager-model-select"
                    value={selectedManagerModel}
                    onChange={(e) => setSelectedManagerModel(e.target.value)}
                    className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
                  >
                    {/* Group models by provider */}
                    {useOllama ? (
                      // Show only Ollama models when Ollama is selected
                      <>
                        <optgroup label="Ollama Models">
                          {Object.entries(availableModels)
                            .filter(([id]) => id.startsWith('ollama:'))
                            .map(([id, name]) => (
                              <option key={id} value={id}>{name}</option>
                            ))}
                        </optgroup>
                      </>
                    ) : (
                      // Show only Groq models when Groq is selected
                      <>
                        <optgroup label="Groq Models">
                          {Object.entries(availableModels)
                            .filter(([id]) => !id.startsWith('ollama:'))
                            .map(([id, name]) => (
                              <option key={id} value={id}>{name}</option>
                            ))}
                        </optgroup>
                      </>
                    )}
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
          {(isLoading || visualizations.length > 0 || plotlyVisualizations.length > 0) && (
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
                {!isLoading && visualizations.length === 0 && plotlyVisualizations.length === 0 && (
                  <div className="text-center py-10 text-gray-500">
                    <p>No visualizations generated yet. Upload a CSV file to start analysis.</p>
                  </div>
                )}

                {/* Plotly Visualizations */}
                {plotlyVisualizations.length > 0 && (
                  <div className="grid grid-cols-1 gap-8">
                    {/* First row - full width for important visualizations */}
                    {plotlyVisualizations.length > 0 && (
                      <CodeVisualization
                        key={`plotly-viz-0`}
                        code={plotlyVisualizations[0].code}
                        figure={plotlyVisualizations[0].figure}
                        output={plotlyVisualizations[0].output}
                        error={plotlyVisualizations[0].error}
                        title={plotlyVisualizations[0].figure?.layout?.title?.text || "Visualization 1"}
                        index={0}
                        onExecute={(code) => handleExecuteCode(code, 0)}
                        isExecuting={isExecutingCode && executingIndex === 0}
                      />
                    )}

                    {/* Second row - two columns for additional visualizations */}
                    {plotlyVisualizations.length > 1 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {plotlyVisualizations.slice(1).map((viz, index) => (
                          <CodeVisualization
                            key={`plotly-viz-${index+1}`}
                            code={viz.code}
                            figure={viz.figure}
                            output={viz.output}
                            error={viz.error}
                            title={viz.figure?.layout?.title?.text || `Visualization ${index+2}`}
                            index={index+1}
                            onExecute={(code) => handleExecuteCode(code, index+1)}
                            isExecuting={isExecutingCode && executingIndex === index+1}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Legacy ECharts Visualizations */}
                {visualizations.length > 0 && plotlyVisualizations.length === 0 && (
                  <div className="grid grid-cols-1 gap-8">
                    {/* First row - full width for important visualizations */}
                    {visualizations.length > 0 && (
                      <div className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                        {/* Add a key to force re-render when visualization changes */}
                        <ReactECharts
                          key={`viz-0-${JSON.stringify(visualizations[0]).substring(0, 20)}`}
                          option={visualizations[0]}
                          style={{ height: 450, width: '100%' }}
                          opts={{ renderer: 'canvas', notMerge: true }}
                          theme="light"
                        />
                        {/* Debug toggle button */}
                        <div className="mt-2 text-right">
                          <button
                            onClick={() => {
                              const debugEl = document.getElementById(`debug-viz-0`);
                              if (debugEl) debugEl.classList.toggle('hidden');
                            }}
                            className="text-xs text-gray-500 hover:text-gray-700"
                          >
                            Toggle Debug
                          </button>
                          <div id={`debug-viz-0`} className="hidden mt-2">
                            <DebugVisualization data={visualizations[0]} />
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Second row - two columns for additional visualizations */}
                    {visualizations.length > 1 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {visualizations.slice(1).map((config: EChartsConfig, index: number) => (
                          <div key={`initial-${index+1}`} className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                            <ReactECharts
                              key={`viz-${index+1}-${JSON.stringify(config).substring(0, 20)}`}
                              option={config}
                              style={{ height: 400, width: '100%' }}
                              opts={{ renderer: 'canvas', notMerge: true }}
                              theme="light"
                            />
                            {/* Debug toggle button */}
                            <div className="mt-2 text-right">
                              <button
                                onClick={() => {
                                  const debugEl = document.getElementById(`debug-viz-${index+1}`);
                                  if (debugEl) debugEl.classList.toggle('hidden');
                                }}
                                className="text-xs text-gray-500 hover:text-gray-700"
                              >
                                Toggle Debug
                              </button>
                              <div id={`debug-viz-${index+1}`} className="hidden mt-2">
                                <DebugVisualization data={config} />
                              </div>
                            </div>
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
          {(isLoadingPrompted || promptedVisualizations.length > 0 || promptedPlotlyVisualizations.length > 0) && (
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
                {!isLoadingPrompted && promptedVisualizations.length === 0 && promptedPlotlyVisualizations.length === 0 && (
                  <div className="text-center py-10 text-gray-500">
                    <p>No custom visualizations generated yet. Enter a specific request.</p>
                  </div>
                )}

                {/* Plotly Prompted Visualizations */}
                {promptedPlotlyVisualizations.length > 0 && (
                  <div className="grid grid-cols-1 gap-8">
                    {/* First prompted visualization - full width */}
                    {promptedPlotlyVisualizations.length > 0 && (
                      <CodeVisualization
                        key={`prompted-plotly-viz-0`}
                        code={promptedPlotlyVisualizations[0].code}
                        figure={promptedPlotlyVisualizations[0].figure}
                        output={promptedPlotlyVisualizations[0].output}
                        error={promptedPlotlyVisualizations[0].error}
                        title={promptedPlotlyVisualizations[0].figure?.layout?.title?.text || "Custom Visualization"}
                        index={plotlyVisualizations.length} // Index after regular visualizations
                        onExecute={(code) => handleExecuteCode(code, plotlyVisualizations.length)}
                        isExecuting={isExecutingCode && executingIndex === plotlyVisualizations.length}
                      />
                    )}

                    {/* Additional prompted visualizations - two columns */}
                    {promptedPlotlyVisualizations.length > 1 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {promptedPlotlyVisualizations.slice(1).map((viz, index) => (
                          <CodeVisualization
                            key={`prompted-plotly-viz-${index+1}`}
                            code={viz.code}
                            figure={viz.figure}
                            output={viz.output}
                            error={viz.error}
                            title={viz.figure?.layout?.title?.text || `Custom Visualization ${index+2}`}
                            index={plotlyVisualizations.length + index + 1}
                            onExecute={(code) => handleExecuteCode(code, plotlyVisualizations.length + index + 1)}
                            isExecuting={isExecutingCode && executingIndex === plotlyVisualizations.length + index + 1}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Legacy ECharts Prompted Visualizations */}
                {promptedVisualizations.length > 0 && promptedPlotlyVisualizations.length === 0 && (
                  <div className="grid grid-cols-1 gap-8">
                    {/* First prompted visualization - full width */}
                    {promptedVisualizations.length > 0 && (
                      <div className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                        <ReactECharts
                          key={`prompted-0-${JSON.stringify(promptedVisualizations[0]).substring(0, 20)}`}
                          option={promptedVisualizations[0]}
                          style={{ height: 450, width: '100%' }}
                          opts={{ renderer: 'canvas', notMerge: true }}
                          theme="light"
                        />
                        {/* Debug toggle button */}
                        <div className="mt-2 text-right">
                          <button
                            onClick={() => {
                              const debugEl = document.getElementById(`debug-prompted-0`);
                              if (debugEl) debugEl.classList.toggle('hidden');
                            }}
                            className="text-xs text-gray-500 hover:text-gray-700"
                          >
                            Toggle Debug
                          </button>
                          <div id={`debug-prompted-0`} className="hidden mt-2">
                            <DebugVisualization data={promptedVisualizations[0]} />
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Additional prompted visualizations - two columns */}
                    {promptedVisualizations.length > 1 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {promptedVisualizations.slice(1).map((config: EChartsConfig, index: number) => (
                          <div key={`prompted-${index+1}`} className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                            <ReactECharts
                              key={`prompted-${index+1}-${JSON.stringify(config).substring(0, 20)}`}
                              option={config}
                              style={{ height: 400, width: '100%' }}
                              opts={{ renderer: 'canvas', notMerge: true }}
                              theme="light"
                            />
                            {/* Debug toggle button */}
                            <div className="mt-2 text-right">
                              <button
                                onClick={() => {
                                  const debugEl = document.getElementById(`debug-prompted-${index+1}`);
                                  if (debugEl) debugEl.classList.toggle('hidden');
                                }}
                                className="text-xs text-gray-500 hover:text-gray-700"
                              >
                                Toggle Debug
                              </button>
                              <div id={`debug-prompted-${index+1}`} className="hidden mt-2">
                                <DebugVisualization data={config} />
                              </div>
                            </div>
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
                <div className="flex items-center gap-2">
                  <CardTitle>Agent Monitor</CardTitle>
                  {hasNewLogs && !showAdminMonitor && (
                    <span className="animate-pulse inline-flex h-3 w-3 rounded-full bg-red-500"></span>
                  )}
                </div>
                <button
                  onClick={() => {
                    setShowAdminMonitor(!showAdminMonitor);
                    // When showing the monitor, clear the new logs indicator and refresh logs
                    if (!showAdminMonitor) {
                      setHasNewLogs(false);
                      fetchAdminLogs();
                    }
                  }}
                  className="text-sm text-gray-600 hover:text-gray-800"
                >
                  {showAdminMonitor ? 'Hide' : 'Show'}
                  {hasNewLogs && !showAdminMonitor && ' (New)'}
                </button>
              </CardHeader>
              <CardContent>
                {showAdminMonitor ? (
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs text-gray-500">
                        {adminLogs.length > 0 ? `${adminLogs.length} log entries` : 'No logs yet'}
                      </span>
                      <div className="flex space-x-3">
                        <button
                          onClick={handleResetBackend}
                          className="text-xs text-red-600 hover:text-red-800 flex items-center"
                          title="Reset backend state, clear logs and cancel any running jobs"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
                            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                            <path d="M3 3v5h5"></path>
                            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"></path>
                            <path d="M16 21h5v-5"></path>
                          </svg>
                          Reset
                        </button>
                        <button
                          onClick={fetchAdminLogs}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          Refresh
                        </button>
                      </div>
                    </div>
                    <AgentConversationMonitor logs={adminLogs} />
                  </div>
                ) : (
                  <div className="text-center py-10 text-gray-500">
                    <p>
                      Agent monitor is hidden.
                      {hasNewLogs && <span className="text-red-500 font-semibold"> New activity detected!</span>}
                    </p>
                    <p>Click "Show" to view agent conversations.</p>
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
