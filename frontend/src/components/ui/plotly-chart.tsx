'use client';

import React, { useEffect, useState, lazy, Suspense } from 'react';

// Lazy load Plotly to improve initial load time
const Plot = lazy(() => import('react-plotly.js'));

export interface PlotlyConfig {
  data: any[];
  layout?: any;
  config?: any;
}

interface PlotlyChartProps {
  plotConfig: PlotlyConfig;
  height?: number;
  width?: string;
  className?: string;
}

export function PlotlyChart({
  plotConfig,
  height = 400,
  width = '100%',
  className = '',
}: PlotlyChartProps) {
  const [mounted, setMounted] = useState(false);
  const [key, setKey] = useState(Date.now());

  // Default layout options
  const defaultLayout = {
    autosize: true,
    margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
      family: 'Inter, sans-serif',
    },
  };

  // Default config options
  const defaultConfig = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
  };

  // Merge default layout with provided layout
  const layout = {
    ...defaultLayout,
    ...plotConfig.layout,
    height,
    width,
  };

  // Merge default config with provided config
  const config = {
    ...defaultConfig,
    ...plotConfig.config,
  };

  // Force remount when plotConfig changes
  useEffect(() => {
    setKey(Date.now());
  }, [plotConfig]);

  // Handle client-side rendering
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div
        style={{ height, width }}
        className={`flex items-center justify-center bg-gray-50 rounded-md ${className}`}
      >
        <div className="animate-pulse text-gray-400">Loading chart...</div>
      </div>
    );
  }
  
  // Handle undefined plotConfig or empty data
  if (!plotConfig || !plotConfig.data || plotConfig.data.length === 0) {
    return (
      <div
        style={{ height, width }}
        className={`flex items-center justify-center bg-gray-50 rounded-md ${className}`}
      >
        <div className="text-gray-400">No data available</div>
      </div>
    );
  }

  return (
    <div className={`plotly-chart-container ${className}`}>
      <Suspense fallback={
        <div style={{ height, width }} className="flex items-center justify-center bg-gray-50 rounded-md">
          <div className="animate-pulse text-gray-400">Loading Plotly...</div>
        </div>
      }>
        <Plot
          key={key}
          data={plotConfig.data}
          layout={layout}
          config={config}
          style={{ width, height }}
          className="w-full"
        />
      </Suspense>
    </div>
  );
}
