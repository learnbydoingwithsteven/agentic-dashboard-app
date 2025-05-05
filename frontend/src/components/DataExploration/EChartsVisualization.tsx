import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { ensureArray, safeMap } from '../../utils/safeArray'; // Import ensureArray and safeMap

interface EChartsVisualizationProps {
  chartConfig: any;
  title?: string;
  height?: string | number;
  width?: string | number;
  loading?: boolean;
}

// Helper function to sanitize chart config to prevent undefined errors
const sanitizeChartConfig = (config: any): any => {
  if (!config || typeof config !== 'object') {
    return {};
  }

  // Create a safe copy of the config
  const safeConfig = { ...config };

  // Ensure series is an array
  if (safeConfig.series) {
    safeConfig.series = safeMap(ensureArray(safeConfig.series), (series: any) => {
      if (!series || typeof series !== 'object') {
        return {};
      }
      // Ensure data in series is an array
      return {
        ...series,
        data: ensureArray(series.data)
      };
    });
  } else {
    safeConfig.series = [];
  }

  // Ensure xAxis is properly formatted
  if (safeConfig.xAxis) {
    if (Array.isArray(safeConfig.xAxis)) {
      safeConfig.xAxis = safeMap(safeConfig.xAxis, (axis: any) => {
        if (!axis || typeof axis !== 'object') {
          return { data: [] };
        }
        return {
          ...axis,
          data: ensureArray(axis.data)
        };
      });
    } else if (typeof safeConfig.xAxis === 'object') {
      safeConfig.xAxis = {
        ...safeConfig.xAxis,
        data: ensureArray(safeConfig.xAxis.data)
      };
    } else {
      safeConfig.xAxis = { data: [] };
    }
  }

  // Ensure yAxis is properly formatted
  if (safeConfig.yAxis) {
    if (Array.isArray(safeConfig.yAxis)) {
      safeConfig.yAxis = safeMap(safeConfig.yAxis, (axis: any) => {
        if (!axis || typeof axis !== 'object') {
          return { data: [] };
        }
        return {
          ...axis,
          data: ensureArray(axis.data)
        };
      });
    } else if (typeof safeConfig.yAxis === 'object') {
      safeConfig.yAxis = {
        ...safeConfig.yAxis,
        data: ensureArray(safeConfig.yAxis.data)
      };
    } else {
      safeConfig.yAxis = { data: [] };
    }
  }

  // Ensure legend is properly formatted
  if (safeConfig.legend) {
    safeConfig.legend = {
      ...safeConfig.legend,
      data: ensureArray(safeConfig.legend.data)
    };
  }

  return safeConfig;
};

// This component takes an ECharts configuration object as a prop and renders the chart using the echarts library.
const EChartsVisualization: React.FC<EChartsVisualizationProps> = ({
  chartConfig,
  title,
  height = '400px',
  width = '100%',
  loading = false,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Reset error state on new config
    setError(null);

    // Log the chart config for debugging
    console.log("EChartsVisualization: chartConfig received", {
      hasConfig: !!chartConfig,
      configType: typeof chartConfig,
      loading
    });

    // Initialize chart
    if (chartRef.current) {
      if (!chartInstance.current) {
        try {
          // Initialize with renderer explicitly set to canvas for better compatibility
          chartInstance.current = echarts.init(chartRef.current, null, {
            renderer: 'canvas',
            useDirtyRect: false // Disable dirty rect optimization for better compatibility
          });
          console.log("EChartsVisualization: Chart instance initialized");
        } catch (error) {
          console.error("Error initializing ECharts:", error);
          setError("Failed to initialize chart");
          return;
        }
      }

      // Set chart options
      if (chartConfig && !loading) {
        try {
          // Validate chartConfig basic structure
          if (!chartConfig || typeof chartConfig !== 'object') {
            console.error("Invalid chart configuration (not an object):", chartConfig);
            setError("Invalid chart configuration: Expected an object.");
            return;
          }

          // Use the sanitizeChartConfig function to create a safer version of the config
          const safeChartConfig = sanitizeChartConfig(chartConfig);

          // Log the sanitized config for debugging
          console.log("EChartsVisualization: Sanitized chart config:", safeChartConfig);

          // Handle dataset if it exists
          if (safeChartConfig.dataset && typeof safeChartConfig.dataset === 'object') {
            safeChartConfig.dataset = {
              ...safeChartConfig.dataset,
              // Ensure dataset.source is an array if dataset exists and has source property
              ...(safeChartConfig.dataset.source && { source: ensureArray(safeChartConfig.dataset.source) })
            };
          }

          // Ensure the chart has a minimum size before rendering
          setTimeout(() => {
            if (chartInstance.current) {
              // Apply the sanitized chart configuration
              chartInstance.current.setOption(safeChartConfig, true); // Use safeChartConfig
              console.log("EChartsVisualization: Chart options set successfully");

              // Force a resize after setting options to ensure proper rendering
              chartInstance.current.resize();
            }
          }, 50);

        } catch (error) {
          // Log the original config for debugging if setOption fails
          console.error("Error setting ECharts options with config:", error, chartConfig);
          setError("Failed to render chart with provided configuration. Check console for details.");
        }
      } else if (loading && chartInstance.current) {
        // Show loading state on the chart itself
        chartInstance.current.showLoading({
          text: 'Loading chart data...',
          color: '#4299e1',
          textColor: '#4a5568',
          maskColor: 'rgba(255, 255, 255, 0.8)',
        });
      } else if (!loading && chartInstance.current) {
        chartInstance.current.hideLoading();
      }
    }

    // Handle resize with debounce for better performance
    const handleResize = () => {
      if (chartInstance.current) {
        try {
          console.log("EChartsVisualization: Resizing chart");
          chartInstance.current.resize();
        } catch (error) {
          console.error("Error resizing chart:", error);
          // Don't set error state for resize issues
        }
      }
    };

    // Debounced resize handler
    let resizeTimeout: NodeJS.Timeout;
    const debouncedResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(handleResize, 100);
    };

    window.addEventListener('resize', debouncedResize);

    // Initial resize after a short delay to ensure container is properly sized
    const initialResizeTimeout = setTimeout(handleResize, 200);

    // Cleanup
    return () => {
      window.removeEventListener('resize', debouncedResize);
      clearTimeout(resizeTimeout);
      clearTimeout(initialResizeTimeout);

      if (chartInstance.current) {
        try {
          console.log("EChartsVisualization: Disposing chart instance");
          chartInstance.current.dispose();
        } catch (error) {
          console.error("Error disposing chart:", error);
        } finally {
          chartInstance.current = null;
        }
      }
    };
  }, [chartConfig, loading]); // Rerun effect if chartConfig or loading state changes

  // Log the chart config for debugging
  console.log('EChartsVisualization: Rendering with config', {
    hasConfig: !!chartConfig,
    configType: typeof chartConfig,
    hasTitle: !!title,
    loading,
    error
  });

  // If there's no chart config, show a message
  if (!chartConfig) {
    return (
      <div style={{ marginBottom: '20px' }}>
        {title && <h3 style={{ textAlign: 'center', marginBottom: '10px' }}>{title}</h3>}
        <div
          style={{
            height,
            width,
            border: '1px solid #f0f0f0',
            borderRadius: '8px',
            padding: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#f9f9f9'
          }}
        >
          <div style={{ color: '#666' }}>No chart configuration available</div>
        </div>
      </div>
    );
  }

  // If there's an error, show an error message
  if (error) {
    return (
      <div style={{ marginBottom: '20px' }}>
        {title && <h3 style={{ textAlign: 'center', marginBottom: '10px' }}>{title}</h3>}
        <Alert variant="destructive">
          <AlertTitle>Chart Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div style={{ marginBottom: '20px', position: 'relative' }} id={`echarts-container-${Date.now()}`}>
      {title && <h3 style={{ textAlign: 'center', marginBottom: '10px' }}>{title}</h3>}
      <div className={loading ? 'opacity-50' : ''}>
        <div
          ref={chartRef}
          style={{
            height,
            width,
            border: '1px solid #f0f0f0',
            borderRadius: '8px',
            padding: '10px',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
          }}
          data-testid="echarts-container"
        />
        {loading && (
          // Centered loading spinner overlay
          <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-50">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EChartsVisualization;
