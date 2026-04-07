import { create } from 'zustand';
import type { AppConfig } from '../types';
import client from '../api/client';

interface ConfigState {
  config: AppConfig | null;
  isLoading: boolean;

  loadConfig: () => Promise<void>;
  updateConfig: (update: Record<string, string>) => Promise<void>;
}

export const useConfigStore = create<ConfigState>((set) => ({
  config: null,
  isLoading: false,

  loadConfig: async () => {
    set({ isLoading: true });
    try {
      const { data } = await client.get('/config');
      set({ config: data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  updateConfig: async (update) => {
    try {
      const { data } = await client.put('/config', update);
      set({ config: data });
    } catch {
      // silent
    }
  },
}));
