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

    // Initialize chart
    if (chartRef.current) {
      if (!chartInstance.current) {
        try {
          chartInstance.current = echarts.init(chartRef.current);
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
          console.log("Sanitized chart config:", safeChartConfig);

          // Handle dataset if it exists
          if (safeChartConfig.dataset && typeof safeChartConfig.dataset === 'object') {
            safeChartConfig.dataset = {
              ...safeChartConfig.dataset,
              // Ensure dataset.source is an array if dataset exists and has source property
              ...(safeChartConfig.dataset.source && { source: ensureArray(safeChartConfig.dataset.source) })
            };
          }

          // Apply the sanitized chart configuration
          chartInstance.current.setOption(safeChartConfig, true); // Use safeChartConfig

        } catch (error) {
          // Log the original config for debugging if setOption fails
          console.error("Error setting ECharts options with config:", error, chartConfig);
          setError("Failed to render chart with provided configuration. Check console for details.");
        }
      } else if (loading && chartInstance.current) {
        // Optionally show loading state on the chart itself
        // chartInstance.current.showLoading();
      } else if (!loading && chartInstance.current) {
        // chartInstance.current.hideLoading();
      }
    }

    // Handle resize
    const handleResize = () => {
      if (chartInstance.current) {
        try {
          chartInstance.current.resize();
        } catch (error) {
          console.error("Error resizing chart:", error);
          // Don't set error state for resize issues
        }
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartInstance.current) {
        try {
          chartInstance.current.dispose();
        } catch (error) {
          console.error("Error disposing chart:", error);
        } finally {
          chartInstance.current = null;
        }
      }
    };
  }, [chartConfig, loading]); // Rerun effect if chartConfig or loading state changes

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
    <div style={{ marginBottom: '20px', position: 'relative' }}> {/* Added position relative for loading overlay */}
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
