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

  // Force remount when plotConfig changes and ensure proper rendering
  useEffect(() => {
    setKey(Date.now());

    // Log the plotConfig for debugging
    console.log('PlotlyChart: plotConfig updated', {
      hasData: plotConfig?.data?.length > 0,
      dataLength: plotConfig?.data?.length,
      layout: plotConfig?.layout ? 'Present' : 'Missing'
    });
  }, [plotConfig]);

  // Handle client-side rendering
  useEffect(() => {
    setMounted(true);

    // Log when component is mounted
    console.log('PlotlyChart: Component mounted');

    // Force a resize event after mounting to ensure proper layout
    const resizeTimeout = setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 100);

    return () => clearTimeout(resizeTimeout);
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

  // If there's no data, show a message
  if (!plotConfig?.data || plotConfig.data.length === 0) {
    return (
      <div className={`plotly-chart-container ${className}`}>
        <div style={{ height, width }} className="flex items-center justify-center bg-gray-50 rounded-md border border-gray-200">
          <div className="text-gray-500">No data available</div>
        </div>
      </div>
    );
  }

  // Log the plotConfig for debugging
  console.log('PlotlyChart: Rendering with config', {
    dataLength: plotConfig.data.length,
    firstDataType: plotConfig.data[0]?.type,
    hasLayout: !!plotConfig.layout,
    mounted
  });

  return (
    <div className={`plotly-chart-container ${className}`}>
      <Suspense fallback={
        <div style={{ height, width }} className="flex items-center justify-center bg-gray-50 rounded-md">
          <div className="animate-pulse text-gray-400">Loading chart...</div>
        </div>
      }>
        <ErrorBoundary fallback={
          <div style={{ height, width }} className="flex items-center justify-center bg-gray-50 rounded-md border border-red-300">
            <div className="text-red-500">Error rendering chart. Check console for details.</div>
          </div>
        }>
          {mounted ? (
            <Plot
              key={key}
              data={plotConfig.data}
              layout={layout}
              config={config}
              style={{ width, height }}
              className="w-full"
              useResizeHandler={true}
              onError={(err) => {
                console.error('Plotly error:', err);
              }}
              onInitialized={(figure) => {
                console.log('Plotly initialized', { hasData: figure.data?.length > 0 });
              }}
              onUpdate={(figure) => {
                console.log('Plotly updated', { hasData: figure.data?.length > 0 });
              }}
            />
          ) : (
            <div style={{ height, width }} className="flex items-center justify-center bg-gray-50 rounded-md">
              <div className="animate-pulse text-gray-400">Loading chart...</div>
            </div>
          )}
        </ErrorBoundary>
      </Suspense>
    </div>
  );
}

// Simple error boundary component for catching render errors
class ErrorBoundary extends React.Component<{ fallback: React.ReactNode, children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { fallback: React.ReactNode, children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('PlotlyChart error boundary caught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}
