import client from './client';
import type { SearchResponse, SearchHistoryItem } from '../types';

export async function searchPapers(params: {
  query: string;
  min_year?: number;
  max_year?: number;
  min_impact_factor?: number;
  max_results?: number;
}): Promise<SearchResponse> {
  const { data } = await client.post('/search', params);
  return data;
}

export interface SearchStreamEvent {
  type: 'status' | 'paper' | 'summary' | 'summary_error' | 'done' | 'error';
  message?: string;
  data?: any;
  paper_id?: number;
  search_id?: number;
  total?: number;
}

export async function* streamSearch(
  params: {
    query: string;
    min_year?: number;
    max_year?: number;
    min_impact_factor?: number;
    max_results?: number;
  },
  autoSummarize: boolean = false,
): AsyncGenerator<SearchStreamEvent> {
  const qs = new URLSearchParams();
  if (autoSummarize) qs.set('auto_summarize', 'true');

  const response = await fetch(`/api/search/stream?${qs.toString()}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
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
          yield JSON.parse(line.slice(6));
        } catch { /* skip */ }
      }
    }
  }
}

export async function getSearchHistory(): Promise<SearchHistoryItem[]> {
  const { data } = await client.get('/search/history');
  return data;
}

export async function deleteSearchHistory(id: number): Promise<void> {
  await client.delete(`/search/history/${id}`);
}

export async function getSearchResults(searchId: number): Promise<SearchResponse> {
  const { data } = await client.get(`/search/${searchId}`);
  return data;
}
