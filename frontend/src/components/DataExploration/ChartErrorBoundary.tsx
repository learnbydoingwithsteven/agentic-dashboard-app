import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';

interface Props {
  children: ReactNode;
  chartTitle?: string; // Optional prop to identify which chart failed
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ChartErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error: error, errorInfo: null }; // Reset errorInfo here
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // You can also log the error to an error reporting service
    console.error("ChartErrorBoundary caught an error:", error, errorInfo);
    console.error("Chart Title (if provided):", this.props.chartTitle);
    // Update state with detailed error info
    this.setState({ error: error, errorInfo: errorInfo });
  }

  public render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        <div style={{ marginBottom: '20px' }}>
          {this.props.chartTitle && <h3 style={{ textAlign: 'center', marginBottom: '10px', color: 'red' }}>{this.props.chartTitle} - Error</h3>}
          <Alert variant="destructive">
            <AlertTitle>Chart Rendering Error</AlertTitle>
            <AlertDescription>
              <p>Something went wrong while rendering this specific chart.</p>
              {this.state.error && (
                <pre style={{ marginTop: '10px', whiteSpace: 'pre-wrap', fontSize: '0.8em' }}>
                  Error: {this.state.error.toString()}
                </pre>
              )}
              {/* Optionally display stack trace for more detail */}
              {/* {this.state.errorInfo && (
                <pre style={{ marginTop: '5px', whiteSpace: 'pre-wrap', fontSize: '0.7em', color: '#555' }}>
                  Stack: {this.state.errorInfo.componentStack}
                </pre>
              )} */}
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ChartErrorBoundary;