import React from 'react';
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
  messages: Message[];
}

interface AgentConversationMonitorProps {
  logs: AdminLog[];
}

export function AgentConversationMonitor({ logs }: AgentConversationMonitorProps) {
  return (
    <div className="overflow-y-auto max-h-[calc(100vh-200px)] space-y-3 text-xs">
      {logs.length === 0 && <p className="text-gray-500 italic">No agent activity logged yet.</p>}
      {logs.map((log, index) => (
        <div key={index} className="mb-4 p-3 border rounded border-gray-200 bg-white shadow-sm">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-2 pb-2 border-b border-gray-100">
            <div className="font-semibold text-sm mb-1 sm:mb-0">
              <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full text-xs mr-2">Run #{logs.length - index}</span>
            </div>
            <div className="flex flex-col sm:flex-row text-xs text-gray-500 space-y-1 sm:space-y-0 sm:space-x-2">
              <span className="bg-gray-100 px-2 py-1 rounded">
                Analyst: <span className="font-mono">{log.analyst_model || 'N/A'}</span>
              </span>
              <span className="bg-gray-100 px-2 py-1 rounded">
                Coder: <span className="font-mono">{log.coder_model || 'N/A'}</span>
              </span>
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
                'default': 'bg-gray-50 border-gray-200 text-gray-800'
              };

              const roleColor = roleColors[msg.role as keyof typeof roleColors] || roleColors.default;
              const roleName = msg.role || 'System';

              return (
                <div key={msgIndex} className={`p-2 rounded border ${roleColor}`}>
                  <div className="flex items-center mb-1">
                    <span className="font-medium text-xs uppercase tracking-wider">{roleName}</span>
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
