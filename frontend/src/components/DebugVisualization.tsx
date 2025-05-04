import React from 'react';
import Plot from 'react-plotly.js';

interface DebugVisualizationProps {
  data: any;
}

export const DebugVisualization: React.FC<DebugVisualizationProps> = ({ data }) => {
  return (
    <div className="bg-gray-100 p-4 rounded-lg overflow-auto max-h-96">
      <h3 className="text-lg font-semibold mb-2">Visualization Debug</h3>
      {data && data.figure ? (
        <Plot
          data={data.figure.data}
          layout={data.figure.layout}
          config={{ responsive: true }}
        />
      ) : (
        <pre className="text-xs whitespace-pre-wrap">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
};
