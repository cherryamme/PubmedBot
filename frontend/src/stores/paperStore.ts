import { create } from 'zustand';
import type { Paper, ChatMessage, FulltextResponse } from '../types';
import { getPaper, getFulltext, summarizePaper, analyzeFulltext } from '../api/papers';
import { getChatHistory, streamChat } from '../api/chat';

interface PaperState {
  paper: Paper | null;
  fulltext: FulltextResponse | null;
  fulltextAnalysis: string | null;
  chatMessages: ChatMessage[];
  chatSessionId: number | null;
  streamingContent: string;
  isLoadingPaper: boolean;
  isLoadingFulltext: boolean;
  isAnalyzing: boolean;
  isSummarizing: boolean;
  isChatting: boolean;
  analyzeError: string | null;

  loadPaper: (id: number) => Promise<void>;
  loadFulltext: (id: number) => Promise<void>;
  doSummarize: (id: number) => Promise<void>;
  doAnalyzeFulltext: (id: number) => Promise<void>;
  loadChatHistory: (paperId: number) => Promise<void>;
  sendMessage: (paperId: number, message: string) => Promise<void>;
  reset: () => void;
}

export const usePaperStore = create<PaperState>((set, get) => ({
  paper: null,
  fulltext: null,
  fulltextAnalysis: null,
  chatMessages: [],
  chatSessionId: null,
  streamingContent: '',
  isLoadingPaper: false,
  isLoadingFulltext: false,
  isAnalyzing: false,
  isSummarizing: false,
  isChatting: false,
  analyzeError: null,

  loadPaper: async (id) => {
    set({ isLoadingPaper: true });
    try {
      const paper = await getPaper(id);
      set({ paper, isLoadingPaper: false });
    } catch {
      set({ isLoadingPaper: false });
    }
  },

  loadFulltext: async (id) => {
    set({ isLoadingFulltext: true });
    try {
      const ft = await getFulltext(id);
      set({ fulltext: ft, isLoadingFulltext: false });
    } catch {
      set({ isLoadingFulltext: false });
    }
  },

  doSummarize: async (id) => {
    set({ isSummarizing: true });
    try {
      const result = await summarizePaper(id);
      set((state) => ({
        paper: state.paper ? { ...state.paper, summary: result } : null,
        isSummarizing: false,
      }));
    } catch {
      set({ isSummarizing: false });
    }
  },

  doAnalyzeFulltext: async (id) => {
    set({ isAnalyzing: true, analyzeError: null });
    try {
      const result = await analyzeFulltext(id);
      set({ fulltextAnalysis: result.analysis, isAnalyzing: false });
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || '分析失败';
      set({ isAnalyzing: false, analyzeError: msg });
    }
  },

  loadChatHistory: async (paperId) => {
    try {
      const sessions = await getChatHistory(paperId);
      if (sessions.length > 0) {
        const latest = sessions[0];
        set({ chatMessages: latest.messages, chatSessionId: latest.session_id });
      }
    } catch { /* silent */ }
  },

  sendMessage: async (paperId, message) => {
    const { chatSessionId } = get();
    const userMsg: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    set((state) => ({
      chatMessages: [...state.chatMessages, userMsg],
      isChatting: true,
      streamingContent: '',
    }));

    try {
      let fullContent = '';
      let newSessionId = chatSessionId;
      for await (const event of streamChat(paperId, message, chatSessionId)) {
        if (event.content) {
          fullContent += event.content;
          set({ streamingContent: fullContent });
        }
        if (event.session_id) newSessionId = event.session_id;
        if (event.done) {
          const assistantMsg: ChatMessage = {
            id: Date.now() + 1,
            role: 'assistant',
            content: fullContent,
            created_at: new Date().toISOString(),
          };
          set((state) => ({
            chatMessages: [...state.chatMessages, assistantMsg],
            chatSessionId: newSessionId,
            streamingContent: '',
            isChatting: false,
          }));
        }
      }
    } catch {
      set({ isChatting: false, streamingContent: '' });
    }
  },

  reset: () => {
    set({
      paper: null, fulltext: null, fulltextAnalysis: null, analyzeError: null,
      chatMessages: [], chatSessionId: null, streamingContent: '',
    });
  },
}));
