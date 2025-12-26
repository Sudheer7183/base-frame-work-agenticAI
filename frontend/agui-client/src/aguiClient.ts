interface AGUIMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, any>;
}

interface AGUIEvent {
  id: string;
  type: string;
  timestamp: string;
  data: any;
}

export class AGUIClient {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  /**
   * Run agent with streaming
   */
  async *runAgent(
    agentId: number,
    threadId: string,
    messages: AGUIMessage[],
    state: Record<string, any> = {}
  ): AsyncGenerator<AGUIEvent> {
    const url = `${this.baseUrl}/agui/agents/${agentId}/run`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify({
        threadId,
        messages,
        state,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            // Event type line
            continue;
          } else if (line.startsWith('data:')) {
            const data = line.substring(5).trim();
            if (data) {
              try {
                const event: AGUIEvent = JSON.parse(data);
                yield event;
              } catch (e) {
                console.error('Failed to parse event:', e);
              }
            }
          } else if (line.startsWith(':')) {
            // Comment/heartbeat - ignore
            continue;
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Get agent state
   */
  async getAgentState(agentId: number, threadId: string): Promise<any> {
    const url = `${this.baseUrl}/agui/agents/${agentId}/state/${threadId}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}