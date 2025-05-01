import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Message {
  name: string | null;
  content: string;
  role: string;
}

interface AdminLog {
  timestamp: string;
  analyst_model?: string;
  coder_model?: string;
  manager_model?: string;
  job_id?: string;
  status?: 'running' | 'completed' | 'cancelled' | 'error';
  messages: Message[];
}

interface AgentConversationMonitorProps {
  logs: AdminLog[];
}

export function AgentConversationMonitor({ logs }: AgentConversationMonitorProps) {
  // Reference to the container div for auto-scrolling
  const containerRef = useRef<HTMLDivElement>(null);

  // State to track if new logs have been added
  const [newLogsAdded, setNewLogsAdded] = useState(false);

  // Track previous log count to detect new logs
  const prevLogCountRef = useRef(logs.length);

  // Auto-scroll to bottom when new logs are added
  useEffect(() => {
    // Check if new logs were added
    if (logs.length > prevLogCountRef.current) {
      setNewLogsAdded(true);

      // Scroll to bottom
      if (containerRef.current) {
        containerRef.current.scrollTop = containerRef.current.scrollHeight;
      }
    }

    // Update previous log count
    prevLogCountRef.current = logs.length;

    // Clear the new logs indicator after a delay
    const timer = setTimeout(() => {
      setNewLogsAdded(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, [logs.length]);

  return (
    <div
      ref={containerRef}
      className={`overflow-y-auto max-h-[calc(100vh-200px)] space-y-3 text-xs ${newLogsAdded ? 'scroll-smooth' : ''}`}
    >
      {logs.length === 0 && <p className="text-gray-500 italic">No agent activity logged yet.</p>}
      {logs.map((log, index) => (
        <div
          key={`log-${index}-${log.timestamp}`}
          className={`mb-4 p-3 border rounded border-gray-200 bg-white shadow-sm ${
            index === 0 && newLogsAdded ? 'animate-pulse-once border-blue-300' : ''
          }`}
        >
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-2 pb-2 border-b border-gray-100">
            <div className="font-semibold text-sm mb-1 sm:mb-0 flex items-center">
              <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full text-xs mr-2">Run #{logs.length - index}</span>
              {log.job_id && (
                <span className="text-xs text-gray-500 mr-2">ID: {log.job_id.substring(0, 8)}</span>
              )}
              {log.status && (
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  log.status === 'completed' ? 'bg-green-100 text-green-800' :
                  log.status === 'running' ? 'bg-blue-100 text-blue-800' :
                  log.status === 'cancelled' ? 'bg-orange-100 text-orange-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {log.status.charAt(0).toUpperCase() + log.status.slice(1)}
                </span>
              )}
            </div>
            <div className="flex flex-col sm:flex-row text-xs text-gray-500 space-y-1 sm:space-y-0 sm:space-x-2">
              <span className="bg-gray-100 px-2 py-1 rounded">
                Analyst: <span className="font-mono">{log.analyst_model || 'N/A'}</span>
              </span>
              <span className="bg-gray-100 px-2 py-1 rounded">
                Coder: <span className="font-mono">{log.coder_model || 'N/A'}</span>
              </span>
              {log.manager_model && (
                <span className="bg-gray-100 px-2 py-1 rounded">
                  Manager: <span className="font-mono">{log.manager_model}</span>
                </span>
              )}
              <span className="bg-gray-100 px-2 py-1 rounded">
                {new Date(log.timestamp).toLocaleString()}
              </span>
            </div>
          </div>
          <div className="space-y-2 pl-2 border-l-2 border-gray-200">
            {log.messages.map((msg, msgIndex) => {
              // Determine agent role and styling
              const roleColors = {
                'User_Proxy': 'bg-blue-50 border-blue-200 text-blue-800',
                'Data_Analyst': 'bg-green-50 border-green-200 text-green-800',
                'Visualization_Coder': 'bg-purple-50 border-purple-200 text-purple-800',
                'GroupChatManager': 'bg-yellow-50 border-yellow-200 text-yellow-800',
                'default': 'bg-gray-50 border-gray-200 text-gray-800'
              };

              const roleColor = roleColors[msg.role as keyof typeof roleColors] || roleColors.default;
              const roleName = msg.role || 'System';

              return (
                <div
                  key={`msg-${index}-${msgIndex}`}
                  className={`p-2 rounded border ${roleColor} ${
                    index === 0 && msgIndex === log.messages.length - 1 && newLogsAdded
                      ? 'border-blue-400'
                      : ''
                  }`}
                >
                  <div className="flex items-center mb-1">
                    <span className="font-medium text-xs uppercase tracking-wider">{roleName}</span>
                    {index === 0 && msgIndex === log.messages.length - 1 && newLogsAdded && (
                      <span className="ml-2 text-xs text-blue-600 font-semibold">NEW</span>
                    )}
                  </div>
                  <pre className="whitespace-pre-wrap break-words font-mono text-xs overflow-auto max-h-[300px]">{msg.content}</pre>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
