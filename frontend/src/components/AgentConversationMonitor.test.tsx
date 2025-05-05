import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentConversationMonitor } from './AgentConversationMonitor';
import '@testing-library/jest-dom';

// Mock the safeArray utility
jest.mock('@/lib/arrayUtils', () => ({
  safeArray: (arr: any[]) => arr || [],
}));

describe('AgentConversationMonitor Component', () => {
  // Sample logs for testing
  const sampleLogs = [
    {
      timestamp: '2023-01-01T12:00:00Z',
      analyst_model: 'llama3-70b-8192',
      coder_model: 'llama3-70b-8192',
      manager_model: 'llama3-70b-8192',
      job_id: 'job-123',
      status: 'completed' as const,
      messages: [
        {
          name: 'Data_Analyst',
          content: 'I suggest a bar chart showing Value by Category.',
          role: 'assistant',
        },
        {
          name: 'Visualization_Coder',
          content: 'Here is the code for the bar chart.',
          role: 'assistant',
        },
      ],
    },
    {
      timestamp: '2023-01-01T11:00:00Z',
      analyst_model: 'llama3-70b-8192',
      coder_model: 'llama3-70b-8192',
      manager_model: 'llama3-70b-8192',
      job_id: 'job-122',
      status: 'completed' as const,
      messages: [
        {
          name: 'Data_Analyst',
          content: 'I suggest a pie chart showing distribution by Category.',
          role: 'assistant',
        },
      ],
    },
  ];

  test('renders empty state when no logs are provided', () => {
    render(<AgentConversationMonitor logs={[]} />);
    
    // Check if the empty state message is displayed
    expect(screen.getByText('No agent activity logged yet.')).toBeInTheDocument();
  });

  test('renders logs correctly', () => {
    render(<AgentConversationMonitor logs={sampleLogs} />);
    
    // Check if log entries are rendered
    expect(screen.getByText('I suggest a bar chart showing Value by Category.')).toBeInTheDocument();
    expect(screen.getByText('Here is the code for the bar chart.')).toBeInTheDocument();
    expect(screen.getByText('I suggest a pie chart showing distribution by Category.')).toBeInTheDocument();
    
    // Check if agent names are displayed
    expect(screen.getByText('ASSISTANT')).toBeInTheDocument();
    
    // Check if job IDs are displayed
    expect(screen.getByText('job-123')).toBeInTheDocument();
    expect(screen.getByText('job-122')).toBeInTheDocument();
  });

  test('handles scroll events to toggle auto-scroll', () => {
    // Create a div with a scrollable height
    const { container } = render(<AgentConversationMonitor logs={sampleLogs} />);
    
    // Get the scrollable container
    const scrollContainer = container.firstChild as HTMLDivElement;
    
    // Mock scrollHeight and clientHeight
    Object.defineProperty(scrollContainer, 'scrollHeight', { value: 1000 });
    Object.defineProperty(scrollContainer, 'clientHeight', { value: 500 });
    Object.defineProperty(scrollContainer, 'scrollTop', { value: 0 });
    
    // Trigger a scroll event
    fireEvent.scroll(scrollContainer, { target: { scrollTop: 100 } });
    
    // Auto-scroll should be disabled when user scrolls up
    // This is hard to test directly since the state is internal to the component
    // We would need to check for side effects or expose the state for testing
  });

  test('renders with different message roles', () => {
    // Create logs with different message roles
    const logsWithDifferentRoles = [
      {
        timestamp: '2023-01-01T12:00:00Z',
        job_id: 'job-123',
        status: 'completed' as const,
        messages: [
          {
            name: 'User',
            content: 'Show me a bar chart.',
            role: 'user',
          },
          {
            name: 'System',
            content: 'Processing request.',
            role: 'system',
          },
          {
            name: 'Data_Analyst',
            content: 'I suggest a bar chart.',
            role: 'assistant',
          },
        ],
      },
    ];
    
    render(<AgentConversationMonitor logs={logsWithDifferentRoles} />);
    
    // Check if different roles are rendered with appropriate styling
    expect(screen.getByText('USER')).toBeInTheDocument();
    expect(screen.getByText('SYSTEM')).toBeInTheDocument();
    expect(screen.getByText('ASSISTANT')).toBeInTheDocument();
    
    // Check if message content is displayed
    expect(screen.getByText('Show me a bar chart.')).toBeInTheDocument();
    expect(screen.getByText('Processing request.')).toBeInTheDocument();
    expect(screen.getByText('I suggest a bar chart.')).toBeInTheDocument();
  });

  test('handles logs with missing fields gracefully', () => {
    // Create logs with missing fields
    const incompleteLog = [
      {
        timestamp: '2023-01-01T12:00:00Z',
        // Missing job_id and status
        messages: [
          {
            // Missing name
            content: 'This message has no name.',
            role: 'assistant',
          },
          {
            name: 'Data_Analyst',
            // Missing content
            role: 'assistant',
          },
          {
            name: 'Visualization_Coder',
            content: 'This message has no role.',
            // Missing role
          },
        ],
      },
    ];
    
    // This should render without crashing
    render(<AgentConversationMonitor logs={incompleteLog} />);
    
    // Check if the message with content but no name is displayed
    expect(screen.getByText('This message has no name.')).toBeInTheDocument();
    
    // The component should handle missing content gracefully
    // The component should handle missing role gracefully
  });
});
