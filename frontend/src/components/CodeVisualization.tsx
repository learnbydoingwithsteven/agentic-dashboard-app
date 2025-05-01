'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PlotlyChart, PlotlyConfig } from '@/components/ui/plotly-chart';
import { Loader2, Play, Code, BarChart } from 'lucide-react';

interface CodeVisualizationProps {
  code: string;
  figure: any;
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
  output = '',
  error = '',
  onExecute,
  isExecuting = false,
  title = 'Visualization',
  index = 0,
}: CodeVisualizationProps) {
  const [activeTab, setActiveTab] = useState<string>('visualization');
  const [codeValue, setCodeValue] = useState<string>(code);
  
  // Convert the figure to a PlotlyConfig
  const plotConfig: PlotlyConfig = {
    data: figure.data || [],
    layout: figure.layout || {},
    config: {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
    },
  };
  
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
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
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
      </CardHeader>
      <CardContent className="p-0">
        <TabsContent value="visualization" className="m-0">
          <div className="p-4">
            {figure && figure.data && figure.data.length > 0 ? (
              <PlotlyChart plotConfig={plotConfig} height={400} />
            ) : (
              <div className="flex items-center justify-center h-[400px] bg-gray-50 rounded-md">
                <div className="text-gray-400">No visualization available</div>
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
      </CardContent>
    </Card>
  );
}
