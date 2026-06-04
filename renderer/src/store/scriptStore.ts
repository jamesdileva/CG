import { create } from 'zustand';

export interface Script {
  id: string;
  topic_id: string;
  content: string | null;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
}

export interface ScriptStore {
  scripts: Map<string, Script>;
  loading: boolean;
  error: string | null;
  setScript: (script: Script) => void;
  updateScript: (id: string, updates: Partial<Script>) => void;
  getScriptForTopic: (topicId: string) => Script | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useScriptStore = create<ScriptStore>((set, get) => ({
  scripts: new Map(),
  loading: false,
  error: null,
  setScript: (script) =>
    set((state) => {
      const newScripts = new Map(state.scripts);
      newScripts.set(script.id, script);
      return { scripts: newScripts };
    }),
  updateScript: (id, updates) =>
    set((state) => {
      const newScripts = new Map(state.scripts);
      const existing = newScripts.get(id);
      if (existing) {
        newScripts.set(id, { ...existing, ...updates });
      }
      return { scripts: newScripts };
    }),
  getScriptForTopic: (topicId) => {
    const scripts = get().scripts;
    for (const script of scripts.values()) {
      if (script.topic_id === topicId) {
        return script;
      }
    }
    return null;
  },
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));
