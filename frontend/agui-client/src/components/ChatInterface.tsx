import React, { useState, useEffect, useRef } from 'react';
import { AGUIClient } from '../services/aguiClient';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  metadata?: any;
}

export const ChatInterface: React.FC<{ agentId: number }> = ({ agentId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentChunk, setCurrentChunk] = useState('');
  const threadId = useRef(generateThreadId());
  const aguiClient = useRef(new AGUIClient(
    'http://localhost:8000',
    localStorage.getItem('token') || ''
  ));

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);
    setCurrentChunk('');

    try {
      const allMessages = [...messages, userMessage];

      // Stream agent response
      for await (const event of aguiClient.current.runAgent(
        agentId,
        threadId.current,
        allMessages,
        {}
      )) {
        handleEvent(event);
      }

      // Finalize message
      if (currentChunk) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: currentChunk,
        }]);
        setCurrentChunk('');
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`,
      }]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleEvent = (event: any) => {
    switch (event.type) {
      case 'message_chunk':
        // Accumulate streaming chunks
        setCurrentChunk(prev => prev + event.data.content);
        break;

      case 'tool_call':
        console.log('Tool called:', event.data.tool);
        // Could show tool execution in UI
        break;

      case 'tool_result':
        console.log('Tool result:', event.data.result);
        break;

      case 'error':
        console.error('Agent error:', event.data.message);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${event.data.message}`,
        }]);
        break;

      case 'completion':
        console.log('Execution completed');
        break;

      default:
        console.log('Unhandled event:', event.type);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {currentChunk && (
          <div className="message assistant streaming">
            {currentChunk}
            <span className="cursor">▊</span>
          </div>
        )}
      </div>
      
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          disabled={isStreaming}
          placeholder="Type your message..."
        />
        <button onClick={handleSend} disabled={isStreaming || !input.trim()}>
          {isStreaming ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

function generateThreadId(): string {
  return `thread_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}