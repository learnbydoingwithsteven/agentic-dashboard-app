import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface AgentLog {
  timestamp: string;
  model: string;
  messages: Array<{
    name: string;
    content: string;
    role: string;
  }>;
}

export function AdminMonitor() {
  const [logs, setLogs] = useState<AgentLog[]>([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/admin/logs');
        if (!response.ok) {
          throw new Error('Failed to fetch logs');
        }
        const data = await response.json();
        setLogs(data.logs);
      } catch (error) {
        console.error('Error fetching logs:', error);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const filteredLogs = logs;

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Agent Activity Monitor</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[600px]">
          {filteredLogs.map((log, index) => (
            <div key={index} className="mb-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex justify-between items-start mb-2">
                <span className="font-medium">Conversation</span>
                <span className="text-sm text-gray-500">{new Date(log.timestamp).toLocaleString()}</span>
              </div>
              <div className="mb-2">
                <span className="font-medium">Model: {log.model}</span>
              </div>
              <div className="space-y-2">
                {log.messages.map((msg, msgIndex) => (
                  <div key={msgIndex} className={`p-2 rounded ${
                    msg.name === 'User' ? 'bg-blue-100' :
                    msg.name === 'Data_Analyst' ? 'bg-green-100' :
                    'bg-gray-50'
                  }`}>
                    <p className="font-medium">{msg.name}</p>
                    <p className="text-sm">{msg.content}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
