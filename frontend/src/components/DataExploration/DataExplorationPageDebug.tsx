import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useApiKey } from '../../hooks/useApiKey';
import EChartsVisualization from './EChartsVisualization';
import ChartErrorBoundary from './ChartErrorBoundary';
import ReactECharts from 'echarts-for-react';

// Define API base URL directly in the component
const API_BASE_URL = "http://localhost:5001/api";

interface DataExplorationProps {
  onBack?: () => void;
  apiKey: string | null; // Add apiKey prop
  useOllama: boolean; // Add useOllama prop
}

const DataExplorationPageDebug: React.FC<DataExplorationProps> = ({ onBack, apiKey, useOllama }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  // Remove useApiKey hook, use props instead
  // const { apiKey } = useApiKey();

  const fetchDataExploration = async () => {
    console.log("DataExplorationPage: Starting data exploration fetch");
    setLoading(true);
    setError(null);

    try {
      const limit = 100; // Limit the number of rows to fetch

      // Use props for API key and Ollama setting
      console.log(`DataExplorationPage: Using Ollama: ${useOllama}`);
      console.log(`DataExplorationPage: API Key: ${apiKey ? 'Present' : 'Missing'}`);

      const url = `${API_BASE_URL}/data_exploration?limit=${limit}`;
      console.log(`DataExplorationPage: Fetching from URL: ${url}`);

      const headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': apiKey || '',
        'USE-OLLAMA': useOllama ? 'true' : 'false',
      };
      console.log("DataExplorationPage: Request headers:", headers);

      const response = await fetch(url, {
        method: 'GET',
        headers,
      });

      console.log(`DataExplorationPage: Response status: ${response.status}`);

      if (!response.ok) {
        let errorMessage = `Failed to fetch data exploration (Status: ${response.status})`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (jsonError) {
          console.error('Error parsing error response:', jsonError);
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log("DataExplorationPage: Received data:", result);

      // Validate the data structure before setting it
      if (!result) {
        throw new Error("Received empty response from server");
      }

      // Ensure the data has the expected structure
      const validatedData = {
        summary: result.summary || {},
        visualizations: result.visualizations || {},
        load_message: result.load_message || "No additional information available"
      };

      setData(validatedData);
    } catch (err: any) {
      console.error('Error fetching data exploration:', err);
      setError(err.message || 'Failed to fetch data exploration');
    } finally {
      setLoading(false);
      console.log("DataExplorationPage: Fetch completed");
    }
  };

  useEffect(() => {
    // Use props for the condition
    if (apiKey || useOllama) {
      console.log("DataExplorationPage: Fetching data with API key or Ollama");
      fetchDataExploration();
    } else {
      console.log("DataExplorationPage: No API key or Ollama configuration found");
      setError("API key or Ollama configuration is required. Please configure your settings first.");
    }
    // Depend on props
  }, [apiKey, useOllama]);

  // Validate data structure when it changes
  useEffect(() => {
    if (data) {
      console.log("DataExplorationPage: Validating data structure");
      // Check if data has the expected structure
      if (!data.summary) {
        console.warn("DataExplorationPage: Missing summary in data");
      }
      if (!data.visualizations) {
        console.warn("DataExplorationPage: Missing visualizations in data");
      }
    }
  }, [data]);

  // Always render the component, even if there's an error
  console.log("DataExplorationPage: Rendering component", {
    loading,
    error: error ? "Error present" : "No error",
    dataPresent: data ? "Data present" : "No data"
  });

  // Simplified debug version that doesn't use any .map() calls
  return (
    <Card className="w-full">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Data Exploration Dashboard</h2>
        {onBack && (
          <Button onClick={onBack} variant="outline">
            Back
          </Button>
        )}
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center p-10">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700"></div>
          <div className="mt-4">Loading visualizations...</div>
        </div>
      )}

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
          <div className="mt-2 flex gap-2">
            <Button onClick={fetchDataExploration} variant="outline" size="sm">
              Retry
            </Button>
            {onBack && (
              <Button onClick={onBack} variant="outline" size="sm">
                Go Back
              </Button>
            )}
          </div>
          {/* Use props for the condition */}
          {!apiKey && !useOllama && (
            <div className="mt-2 text-sm">
              <p>No API key or Ollama configuration found. Please configure your API settings first.</p>
            </div>
          )}
        </Alert>
      )}

      {data && !loading && (
        <div className="p-6">
          <Tabs defaultValue="visualizations">
            <TabsList className="mb-4">
              <TabsTrigger value="visualizations">Visualizations</TabsTrigger>
              <TabsTrigger value="debug">Debug Info</TabsTrigger>
            </TabsList>

            <TabsContent value="visualizations">
              <div className="grid grid-cols-1 gap-8">
                {/* Province Commitments Chart */}
                {data.visualizations?.province_commitments && (
                  <div className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                    <h3 className="text-lg font-semibold mb-4 text-center">
                      {data.visualizations.province_commitments?.title?.text || "Province Commitments"}
                    </h3>
                    <ChartErrorBoundary chartTitle="Province Commitments">
                      <ReactECharts
                        option={data.visualizations.province_commitments}
                        style={{ height: 450, width: '100%' }}
                        opts={{ renderer: 'canvas' }}
                        theme="light"
                      />
                    </ChartErrorBoundary>
                  </div>
                )}

                {/* Expense Types Chart */}
                {data.visualizations?.expense_types && (
                  <div className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                    <h3 className="text-lg font-semibold mb-4 text-center">
                      {data.visualizations.expense_types?.title?.text || "Expense Types"}
                    </h3>
                    <ChartErrorBoundary chartTitle="Expense Types">
                      <ReactECharts
                        option={data.visualizations.expense_types}
                        style={{ height: 450, width: '100%' }}
                        opts={{ renderer: 'canvas' }}
                        theme="light"
                      />
                    </ChartErrorBoundary>
                  </div>
                )}

                {/* Payment Comparison Chart */}
                {data.visualizations?.payment_comparison && (
                  <div className="border p-4 rounded-lg shadow-md bg-white hover:shadow-lg transition-shadow">
                    <h3 className="text-lg font-semibold mb-4 text-center">
                      {data.visualizations.payment_comparison?.title?.text || "Payment Comparison"}
                    </h3>
                    <ChartErrorBoundary chartTitle="Payment Comparison">
                      <ReactECharts
                        option={data.visualizations.payment_comparison}
                        style={{ height: 450, width: '100%' }}
                        opts={{ renderer: 'canvas' }}
                        theme="light"
                      />
                    </ChartErrorBoundary>
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="debug">
              <Alert>
                <AlertTitle>Debug Information</AlertTitle>
                <AlertDescription>
                  <p>Data has been loaded successfully. This is the raw data structure.</p>
                  <p className="mt-2">Data structure:</p>
                  <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto max-h-[300px]">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </AlertDescription>
              </Alert>
            </TabsContent>
          </Tabs>
        </div>
      )}

      {!data && !loading && !error && (
        <div className="flex flex-col items-center justify-center p-10">
          <div className="text-center text-gray-500">
            <p className="mb-4">No data available. Please upload a dataset first.</p>
            {onBack && (
              <Button onClick={onBack} variant="outline">
                Go Back to Upload
              </Button>
            )}
          </div>
        </div>
      )}
    </Card>
  );
};

export default DataExplorationPageDebug;
