import client from './client';
import type { Paper, FulltextResponse, SummarizeResult } from '../types';

export async function getPaper(id: number): Promise<Paper> {
  const { data } = await client.get(`/papers/${id}`);
  return data;
}

export async function getFulltext(id: number): Promise<FulltextResponse> {
  const { data } = await client.get(`/papers/${id}/fulltext`);
  return data;
}

export async function summarizePaper(id: number): Promise<SummarizeResult> {
  const { data } = await client.post(`/papers/${id}/summarize`);
  return data;
}

export async function analyzeFulltext(id: number): Promise<{ analysis: string; model_used: string }> {
  const { data } = await client.post(`/papers/${id}/analyze-fulltext`);
  return data;
}

export async function summarizeAll(searchId: number): Promise<any> {
  const { data } = await client.post(`/papers/search/${searchId}/summarize-all`);
  return data;
}
