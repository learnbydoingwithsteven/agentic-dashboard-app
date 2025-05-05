'use client';

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PlotlyChart, PlotlyConfig } from '@/components/ui/plotly-chart';
import { Loader2, Play, Code, BarChart } from 'lucide-react';
import EChartsVisualization from '@/components/DataExploration/EChartsVisualization';

interface CodeVisualizationProps {
  code: string;
  figure?: any;
  echartsConfig?: any;
  output?: string;
  error?: string;
  onExecute?: (code: string) => Promise<void>;
  isExecuting?: boolean;
  title?: string;
  index?: number;
}

export function CodeVisualization({
  code,
  figure,
  echartsConfig,
  output = '',
  error = '',
  onExecute,
  isExecuting = false,
  title = 'Visualization',
  index = 0,
}: CodeVisualizationProps) {
  const [activeTab, setActiveTab] = useState<string>('visualization');
  const [codeValue, setCodeValue] = useState<string>(code);

  // Convert the figure to a PlotlyConfig with better error handling
  const plotConfig: PlotlyConfig = useMemo(() => {
    // Log the figure for debugging
    console.log('CodeVisualization: Processing figure', {
      hasFigure: !!figure,
      figureType: typeof figure,
      hasData: figure?.data?.length > 0,
      hasLayout: !!figure?.layout
    });

    if (!figure) {
      return {
        data: [],
        layout: {},
        config: {
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
        },
      };
    }

    try {
      // Ensure data is an array
      const safeData = Array.isArray(figure.data) ? figure.data : [];

      // Ensure each trace has the required properties
      const processedData = safeData.map(trace => {
        // If trace is null or undefined, return an empty object
        if (!trace) return {};

        // Ensure x and y are arrays if they exist
        const safeTrace = { ...trace };
        if (safeTrace.x && !Array.isArray(safeTrace.x)) {
          safeTrace.x = [safeTrace.x];
        }
        if (safeTrace.y && !Array.isArray(safeTrace.y)) {
          safeTrace.y = [safeTrace.y];
        }

        // Ensure type is set
        if (!safeTrace.type) {
          safeTrace.type = 'scatter';
        }

        return safeTrace;
      });

      // Ensure layout has minimum required properties
      const safeLayout = {
        title: figure.layout?.title || 'Chart',
        autosize: true,
        margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 },
        ...figure.layout
      };

      return {
        data: processedData,
        layout: safeLayout,
        config: {
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
        },
      };
    } catch (error) {
      console.error('Error processing Plotly figure:', error);
      // Return a minimal valid configuration
      return {
        data: [{ type: 'scatter', x: [1, 2, 3], y: [1, 2, 3], mode: 'lines+markers', name: 'Error Fallback' }],
        layout: { title: 'Error Processing Figure' },
        config: {
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
        },
      };
    }
  }, [figure]);

  const handleExecute = async () => {
    if (onExecute) {
      await onExecute(codeValue);
    }
  };

  return (
    <Card className="w-full overflow-hidden">
      <CardHeader className="bg-gray-50 border-b pb-3">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg font-medium">{title}</CardTitle>
          <div className="w-auto">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList>
                <TabsTrigger value="visualization" className="flex items-center gap-1">
                  <BarChart className="h-4 w-4" />
                  <span className="hidden sm:inline">Visualization</span>
                </TabsTrigger>
                <TabsTrigger value="code" className="flex items-center gap-1">
                  <Code className="h-4 w-4" />
                  <span className="hidden sm:inline">Code</span>
                </TabsTrigger>
                {output && (
                  <TabsTrigger value="output" className="flex items-center gap-1">
                    <span className="hidden sm:inline">Output</span>
                  </TabsTrigger>
                )}
              </TabsList>
            </Tabs>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsContent value="visualization" className="m-0">
            <div className="p-4">
              {/* Plotly Visualization */}
              {figure && figure.data && figure.data.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-gray-500 mb-2">Plotly Visualization</h3>
                  <PlotlyChart plotConfig={plotConfig} height={400} />
                </div>
              )}

              {/* ECharts Visualization */}
              {echartsConfig && (
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-gray-500 mb-2">ECharts Visualization</h3>
                  <EChartsVisualization chartConfig={echartsConfig} height={400} />
                </div>
              )}

              {/* No visualizations available */}
              {(!figure || !figure.data || figure.data.length === 0) && !echartsConfig && (
                <div className="flex items-center justify-center h-[400px] bg-gray-50 rounded-md">
                  <div className="text-gray-400">
                    {error && error.includes("Columns not found") ? (
                      <div className="text-center">
                        <p className="text-red-500 font-medium mb-2">{error}</p>
                        <p className="text-sm">The dataset might be using different column names. Try using the exact column names from the dataset.</p>
                      </div>
                    ) : error ? (
                      <div className="text-center">
                        <p className="text-red-500 font-medium mb-2">Error occurred</p>
                        <p className="text-sm">{error}</p>
                      </div>
                    ) : (
                      "No visualization available"
                    )}
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="code" className="m-0">
            <div className="p-4 flex flex-col gap-4">
              <div className="relative">
                <pre className="p-4 bg-gray-50 rounded-md overflow-auto max-h-[400px] text-sm">
                  <code>{codeValue}</code>
                </pre>
                {onExecute && (
                  <div className="absolute top-2 right-2">
                    <Button
                      size="sm"
                      onClick={handleExecute}
                      disabled={isExecuting}
                      className="flex items-center gap-1"
                    >
                      {isExecuting ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Running...</span>
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" />
                          <span>Run Code</span>
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </div>

              {error && (
                <div className="p-4 bg-red-50 text-red-800 rounded-md overflow-auto max-h-[200px] text-sm">
                  <h4 className="font-medium mb-2">Error:</h4>
                  <pre>{error}</pre>
                </div>
              )}
            </div>
          </TabsContent>

          {output && (
            <TabsContent value="output" className="m-0">
              <div className="p-4">
                <pre className="p-4 bg-gray-50 rounded-md overflow-auto max-h-[400px] text-sm">
                  <code>{output}</code>
                </pre>
              </div>
            </TabsContent>
          )}
        </Tabs>
      </CardContent>
    </Card>
  );
}
