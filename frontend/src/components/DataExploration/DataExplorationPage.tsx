import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import EChartsVisualization from './EChartsVisualization';
import ChartErrorBoundary from './ChartErrorBoundary'; // Import the Error Boundary
import { useApiKey } from '../../hooks/useApiKey';
import { safeMap, ensureArray } from '../../utils/safeArray';

// Define API base URL directly in the component
const API_BASE_URL = "http://localhost:5001/api";

interface DataExplorationProps {
  onBack?: () => void;
}

const DataExplorationPage: React.FC<DataExplorationProps> = ({ onBack }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const { apiKey } = useApiKey();

  const fetchDataExploration = async () => {
    console.log("DataExplorationPage: Starting data exploration fetch");
    setLoading(true);
    setError(null);

    try {
      const limit = 100; // Limit the number of rows to fetch

      // Check if we're using Ollama
      const useOllama = localStorage.getItem('useOllama') === 'true';
      console.log(`DataExplorationPage: Using Ollama: ${useOllama}`);

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
    // Only fetch if we have an API key or if we're using Ollama
    // This prevents the component from making API calls without authentication
    const useOllama = localStorage.getItem('useOllama') === 'true';

    if (apiKey || useOllama) {
      console.log("DataExplorationPage: Fetching data with API key or Ollama");
      fetchDataExploration();
    } else {
      // Set an error message if no API key is available
      console.log("DataExplorationPage: No API key or Ollama configuration found");
      setError("API key is required. Please configure your API key in the settings.");
    }
  }, [apiKey]);

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

  // --- Corrected renderDataSummary with proper try-catch nesting ---
  const renderDataSummary = () => {
    if (!data || !data.summary) return null;

    // Outer try-catch to catch any error during summary rendering
    try {
      // Inner try-catch specifically for potential errors during destructuring/initial processing
      try {
        // Safely destructure with default values to prevent undefined errors
        const {
          num_rows = 0,
          num_cols = 0,
          columns = [],
          numeric_stats = {},
          categorical_stats = {},
          sample_data = []
        } = data.summary || {};

        // Safely get column keys with fallbacks
        const numericColumns = numeric_stats && typeof numeric_stats === 'object' ? Object.keys(numeric_stats) : [];
        const categoricalColumns = categorical_stats && typeof categorical_stats === 'object' ? Object.keys(categorical_stats) : [];

        // Ensure columns and sample_data are arrays
        const safeColumns = ensureArray(columns) as string[];
        const safeSampleData = ensureArray(sample_data) as any[];

        // Return the JSX for the summary tables
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 border rounded-lg bg-gray-50">
              <div className="flex flex-col">
                <span className="text-sm text-gray-500">Rows</span>
                <span className="text-lg font-medium">{(num_rows || 0).toLocaleString()}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-sm text-gray-500">Columns</span>
                <span className="text-lg font-medium">{num_cols || 0}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-sm text-gray-500">Numeric Columns</span>
                <span className="text-lg font-medium">{numericColumns.length}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-sm text-gray-500">Categorical Columns</span>
                <span className="text-lg font-medium">{categoricalColumns.length}</span>
              </div>
            </div>

            {numericColumns.length > 0 && (
              <div>
                <h3 className="text-lg font-medium mb-2">Numeric Columns Statistics</h3>
                <div className="overflow-x-auto max-h-[500px] border rounded-md shadow-sm">
                  <div className="min-w-max">
                    <table className="w-full border-collapse">
                      <thead className="sticky top-0 bg-white">
                        <tr className="bg-gray-100">
                          <th className="border p-2 text-left">Column</th>
                          <th className="border p-2 text-left">Min</th>
                          <th className="border p-2 text-left">Max</th>
                          <th className="border p-2 text-left">Mean</th>
                          <th className="border p-2 text-left">Median</th>
                          <th className="border p-2 text-left">Missing</th>
                        </tr>
                      </thead>
                      <tbody>
                        {safeMap(numericColumns, (column) => (
                          <tr key={column} className="hover:bg-gray-50">
                            <td className="border p-2">{column}</td>
                            <td className="border p-2">{numeric_stats && numeric_stats[column]?.min?.toLocaleString() || 'N/A'}</td>
                            <td className="border p-2">{numeric_stats && numeric_stats[column]?.max?.toLocaleString() || 'N/A'}</td>
                            <td className="border p-2">{numeric_stats && numeric_stats[column]?.mean?.toLocaleString() || 'N/A'}</td>
                            <td className="border p-2">{numeric_stats && numeric_stats[column]?.median?.toLocaleString() || 'N/A'}</td>
                            <td className="border p-2">{numeric_stats && numeric_stats[column]?.missing?.toLocaleString() || '0'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {safeColumns.length > 0 && safeSampleData.length > 0 && (
              <div>
                <h3 className="text-lg font-medium mb-2">Sample Data</h3>
                <div className="overflow-x-auto max-h-[500px] border rounded-md shadow-sm">
                  <div className="min-w-max">
                    <table className="w-full border-collapse">
                      <thead className="sticky top-0 bg-white">
                        <tr className="bg-gray-100">
                          {safeMap(safeColumns, (col: string) => (
                            <th key={col} className="border p-2 text-left">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {safeMap(safeSampleData, (row: any, index: number) => (
                          <tr key={index} className="hover:bg-gray-50">
                            {safeMap(safeColumns, (col: string) => (
                              <td key={`${index}-${col}`} className="border p-2 whitespace-nowrap">
                                {row && row[col] !== undefined ? row[col] : 'N/A'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      } catch (innerError) {
        // Catch errors from the inner rendering logic (destructuring, mapping, etc.)
        console.error("Inner error rendering data summary details:", innerError);
        // Return a specific error message for inner failures
        return (
          <Alert variant="destructive" className="mb-4">
            <AlertTitle>Data Summary Processing Error</AlertTitle>
            <AlertDescription>
              <p>Failed to process summary data for display.</p>
              <p className="text-sm mt-2">{innerError instanceof Error ? innerError.message : 'Unknown processing error'}</p>
            </AlertDescription>
          </Alert>
        );
      }
    } catch (outerError) {
      // Catch any unexpected errors from the entire function
      console.error("Outer CRITICAL ERROR rendering data summary:", outerError);
      return (
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>Error Rendering Summary Component</AlertTitle>
          <AlertDescription>
            <p>Failed to display the data summary section due to an unexpected error.</p>
            {/* Type check for error message */}
            <p className="text-sm mt-2">
              {outerError instanceof Error ? outerError.message : String(outerError)}
            </p>
          </AlertDescription>
        </Alert>
      );
    }
  };
  // --- End corrected renderDataSummary ---


  const renderVisualizations = () => {
    if (!data || !data.visualizations) return null;

    try {
      // Safely destructure with default empty objects
      const {
        province_commitments = {},
        expense_types = {},
        payment_comparison = {}
      } = data.visualizations || {};

      // Check if each chart config is valid (has at least some properties)
      const hasProvinceCommitments = province_commitments && typeof province_commitments === 'object' && Object.keys(province_commitments).length > 0;
      const hasExpenseTypes = expense_types && typeof expense_types === 'object' && Object.keys(expense_types).length > 0;
      const hasPaymentComparison = payment_comparison && typeof payment_comparison === 'object' && Object.keys(payment_comparison).length > 0;

      // If no valid visualizations, show a message
      if (!hasProvinceCommitments && !hasExpenseTypes && !hasPaymentComparison) {
        return (
          <div className="p-6 text-center text-gray-500">
            <p>No visualizations available for this dataset.</p>
          </div>
        );
      }

      // Ensure chart configs have necessary array properties (like series)
      // using ensureArray for safety before passing to EChartsVisualization
      const safeProvinceCommitments = {
        ...province_commitments,
        series: ensureArray(province_commitments?.series || []),
        xAxis: province_commitments?.xAxis ? {
          ...province_commitments.xAxis,
          data: ensureArray(province_commitments.xAxis?.data || [])
        } : { data: [] },
        yAxis: province_commitments?.yAxis ? {
          ...province_commitments.yAxis,
          data: ensureArray(province_commitments.yAxis?.data || [])
        } : { data: [] },
        legend: province_commitments?.legend ? {
          ...province_commitments.legend,
          data: ensureArray(province_commitments.legend?.data || [])
        } : { data: [] }
      };

      const safeExpenseTypes = {
        ...expense_types,
        series: ensureArray(expense_types?.series || []),
        xAxis: expense_types?.xAxis ? {
          ...expense_types.xAxis,
          data: ensureArray(expense_types.xAxis?.data || [])
        } : { data: [] },
        yAxis: expense_types?.yAxis ? {
          ...expense_types.yAxis,
          data: ensureArray(expense_types.yAxis?.data || [])
        } : { data: [] },
        legend: expense_types?.legend ? {
          ...expense_types.legend,
          data: ensureArray(expense_types.legend?.data || [])
        } : { data: [] }
      };

      const safePaymentComparison = {
        ...payment_comparison,
        series: ensureArray(payment_comparison?.series || []),
        xAxis: payment_comparison?.xAxis ? {
          ...payment_comparison.xAxis,
          data: ensureArray(payment_comparison.xAxis?.data || [])
        } : { data: [] },
        yAxis: payment_comparison?.yAxis ? {
          ...payment_comparison.yAxis,
          data: ensureArray(payment_comparison.yAxis?.data || [])
        } : { data: [] },
        legend: payment_comparison?.legend ? {
          ...payment_comparison.legend,
          data: ensureArray(payment_comparison.legend?.data || [])
        } : { data: [] }
      };

      // Additional safety check for series items that might contain data arrays
      // Use safeMap and add stricter checks within the map function
      safeProvinceCommitments.series = safeMap(safeProvinceCommitments.series, (series: any) => {
        // Ensure series is a non-null object before accessing properties
        if (series !== null && typeof series === 'object') {
          return {
            ...series,
            data: ensureArray(series.data || []) // Ensure data exists and is an array
          };
        }
        // Log problematic item and return it (or a default like { data: [] })
        console.warn("DataExplorationPage: Encountered invalid item in province_commitments series:", series);
        return series; // Returning the invalid item might still cause ECharts errors, but prevents the map crash here. Consider returning { data: [] } if needed.
      });

      safeExpenseTypes.series = safeMap(safeExpenseTypes.series, (series: any) => {
        // Ensure series is a non-null object before accessing properties
        if (series !== null && typeof series === 'object') {
          return {
            ...series,
            data: ensureArray(series.data || []) // Ensure data exists and is an array
          };
        }
        // Log problematic item and return it
        console.warn("DataExplorationPage: Encountered invalid item in expense_types series:", series);
        return series;
      });

      safePaymentComparison.series = safeMap(safePaymentComparison.series, (series: any) => {
        // Ensure series is a non-null object before accessing properties
        if (series !== null && typeof series === 'object') {
          return {
            ...series,
            data: ensureArray(series.data || []) // Ensure data exists and is an array
          };
        }
        // Log problematic item and return it
        console.warn("DataExplorationPage: Encountered invalid item in payment_comparison series:", series);
        return series;
      });

      // --- Add detailed logging ---
      console.log("renderVisualizations: Raw data.visualizations:", data?.visualizations);
      console.log("renderVisualizations: Destructured province_commitments:", province_commitments);
      console.log("renderVisualizations: Destructured expense_types:", expense_types);
      console.log("renderVisualizations: Destructured payment_comparison:", payment_comparison);
      console.log("renderVisualizations: Final safeProvinceCommitments:", safeProvinceCommitments);
      console.log("renderVisualizations: Final safeExpenseTypes:", safeExpenseTypes);
      console.log("renderVisualizations: Final safePaymentComparison:", safePaymentComparison);
      // --- End detailed logging ---

      return (
        <div className="space-y-6 overflow-auto">
          {hasProvinceCommitments && (
            <div className="visualization-container">
              <ChartErrorBoundary chartTitle="Province Commitments Distribution">
                <EChartsVisualization
                  chartConfig={safeProvinceCommitments}
                  title="Province Commitments Distribution"
                  height={400}
                />
              </ChartErrorBoundary>
            </div>
          )}
          {hasExpenseTypes && (
            <div className="visualization-container">
              <ChartErrorBoundary chartTitle="Expense Types">
                <EChartsVisualization
                  chartConfig={safeExpenseTypes}
                  title="Expense Types"
                  height={400}
                />
              </ChartErrorBoundary>
            </div>
          )}
          {hasPaymentComparison && (
            <div className="visualization-container">
              <ChartErrorBoundary chartTitle="Commitments and Payments Comparison">
                <EChartsVisualization
                  chartConfig={safePaymentComparison}
                  title="Commitments and Payments Comparison"
                  height={400}
                />
              </ChartErrorBoundary>
            </div>
          )}
        </div>
      );
    } catch (error) {
      console.error("Error rendering visualizations:", error);
      return (
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            <p>Failed to render visualizations.</p>
            <p className="text-sm mt-2">{error instanceof Error ? error.message : 'Unknown error'}</p>
          </AlertDescription>
        </Alert>
      );
    }
  };

  // Always render the component, even if there's an error
  console.log("DataExplorationPage: Rendering component", {
    loading,
    error: error ? "Error present" : "No error",
    dataPresent: data ? "Data present" : "No data"
  });

  try {
    return (
      <Card className="w-full">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Data Exploration</h2>
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
            {!apiKey && localStorage.getItem('useOllama') !== 'true' && (
              <div className="mt-2 text-sm">
                <p>No API key or Ollama configuration found. Please configure your API settings first.</p>
              </div>
            )}
          </Alert>
        )}

        {data && !loading && (
          <Tabs defaultValue="visualizations" className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="visualizations">Visualizations</TabsTrigger>
              <TabsTrigger value="summary">Data Summary</TabsTrigger>
              <TabsTrigger value="info">Information</TabsTrigger>
            </TabsList>
            <TabsContent value="visualizations">
              {renderVisualizations()}
            </TabsContent>
            <TabsContent value="summary">
              {renderDataSummary()}
            </TabsContent>
            <TabsContent value="info">
              <Alert className="mb-4">
                <AlertTitle>Dataset Information</AlertTitle>
                <AlertDescription>{data.load_message || 'No additional information available for this dataset.'}</AlertDescription>
              </Alert>
            </TabsContent>
          </Tabs>
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
  } catch (renderError) {
    console.error("Error rendering DataExplorationPage:", renderError);
    return (
      <Card className="w-full">
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>Rendering Error</AlertTitle>
          <AlertDescription>
            <p>An error occurred while rendering the data exploration page.</p>
            <p className="text-sm mt-2">{renderError instanceof Error ? renderError.message : 'Unknown error'}</p>
            <div className="mt-4">
              <Button onClick={fetchDataExploration} variant="outline" size="sm">
                Retry
              </Button>
              {onBack && (
                <Button onClick={onBack} variant="outline" size="sm" className="ml-2">
                  Go Back
                </Button>
              )}
            </div>
          </AlertDescription>
        </Alert>
      </Card>
    );
  }
};

export default DataExplorationPage;
