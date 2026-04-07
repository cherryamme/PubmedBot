import { create } from 'zustand';
import type { Paper, SearchHistoryItem } from '../types';
import { streamSearch, getSearchHistory, getSearchResults } from '../api/search';
import { summarizeAll } from '../api/papers';

interface SearchState {
  query: string;
  minYear: number;
  maxYear: number;
  minIF: number;
  maxResults: number;
  results: Paper[];
  searchId: number | null;
  isLoading: boolean;
  isSummarizing: boolean;
  autoSummarize: boolean;
  statusMessage: string;
  error: string | null;
  history: SearchHistoryItem[];

  setQuery: (q: string) => void;
  setMinYear: (y: number) => void;
  setMaxYear: (y: number) => void;
  setMinIF: (v: number) => void;
  setMaxResults: (v: number) => void;
  setAutoSummarize: (v: boolean) => void;
  doSearch: () => Promise<void>;
  loadHistory: () => Promise<void>;
  deleteHistory: (id: number) => Promise<void>;
  loadSearchResults: (id: number) => Promise<void>;
  doSummarizeAll: () => Promise<void>;
  updatePaperSummary: (paperId: number, summary: any) => void;
}

const currentYear = new Date().getFullYear();

export const useSearchStore = create<SearchState>((set, get) => ({
  query: '',
  minYear: currentYear - 2,
  maxYear: currentYear,
  minIF: 0,
  maxResults: 50,
  results: [],
  searchId: null,
  isLoading: false,
  isSummarizing: false,
  autoSummarize: false,
  statusMessage: '',
  error: null,
  history: [],

  setQuery: (q) => set({ query: q }),
  setMinYear: (y) => set({ minYear: y }),
  setMaxYear: (y) => set({ maxYear: y }),
  setMinIF: (v) => set({ minIF: v }),
  setMaxResults: (v) => set({ maxResults: v }),
  setAutoSummarize: (v) => set({ autoSummarize: v }),

  doSearch: async () => {
    const { query, minYear, maxYear, minIF, maxResults, autoSummarize } = get();
    if (!query.trim()) return;
    set({ isLoading: true, error: null, results: [], searchId: null, statusMessage: '正在检索...' });

    try {
      for await (const event of streamSearch(
        {
          query: query.trim(),
          min_year: minYear || undefined,
          max_year: maxYear || undefined,
          min_impact_factor: minIF > 0 ? minIF : undefined,
          max_results: maxResults,
        },
        autoSummarize,
      )) {
        switch (event.type) {
          case 'status':
            set({ statusMessage: event.message || '' });
            break;
          case 'paper':
            set((state) => ({
              results: [...state.results, event.data as Paper],
              statusMessage: `已加载 ${state.results.length + 1} 篇...`,
            }));
            break;
          case 'summary':
            set((state) => ({
              results: state.results.map((p) =>
                p.id === event.paper_id ? { ...p, summary: event.data } : p
              ),
            }));
            break;
          case 'done':
            set({ searchId: event.search_id || null, isLoading: false, statusMessage: '' });
            get().loadHistory();
            break;
          case 'error':
            set({ error: event.message || '搜索失败', isLoading: false, statusMessage: '' });
            break;
        }
      }
    } catch (e: any) {
      set({ error: e.message || '搜索失败', isLoading: false, statusMessage: '' });
    }
  },

  loadHistory: async () => {
    try {
      const history = await getSearchHistory();
      set({ history });
    } catch { /* silent */ }
  },

  deleteHistory: async (id: number) => {
    // Only remove from display list, keep in database
    set((state) => ({ history: state.history.filter((h) => h.id !== id) }));
  },

  loadSearchResults: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      const resp = await getSearchResults(id);
      set({ results: resp.papers, searchId: resp.search_id, query: resp.query, isLoading: false });
    } catch (e: any) {
      set({ error: e?.response?.data?.detail || '加载失败', isLoading: false });
    }
  },

  doSummarizeAll: async () => {
    const { searchId } = get();
    if (!searchId) return;
    set({ isSummarizing: true });
    try {
      await summarizeAll(searchId);
      const resp = await getSearchResults(searchId);
      set({ results: resp.papers, isSummarizing: false });
    } catch {
      set({ isSummarizing: false });
    }
  },

  updatePaperSummary: (paperId, summary) => {
    set((state) => ({
      results: state.results.map((p) =>
        p.id === paperId ? { ...p, summary } : p
      ),
    }));
  },
}));
