import type { ChatMessage, ChatStreamEvent } from '../types';
import client from './client';

export async function getChatHistory(paperId: number): Promise<{ session_id: number; messages: ChatMessage[] }[]> {
  const { data } = await client.get(`/papers/${paperId}/chat/history`);
  return data;
}

export async function* streamChat(
  paperId: number,
  message: string,
  sessionId?: number | null,
): AsyncGenerator<ChatStreamEvent> {
  const response = await fetch(`/api/papers/${paperId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.body) throw new Error('No response body');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event: ChatStreamEvent = JSON.parse(line.slice(6));
          yield event;
        } catch {
          // skip malformed events
        }
      }
    }
  }
}
