import React from 'react';
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotChat } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

export default function App() {
  return (
    <CopilotKit
      runtimeUrl="/agui/agents/1/run"
      agent="my-agent"
    >
      <div style={{ height: '100vh' }}>
        <CopilotChat
          labels={{
            title: "AI Agent Assistant",
            initial: "Hi! I'm your AI assistant. How can I help you today?",
          }}
        />
      </div>
    </CopilotKit>
  );
}

