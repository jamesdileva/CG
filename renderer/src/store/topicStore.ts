import { create } from 'zustand';

export interface Topic {
  id: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  embedding: null;
}

export interface TopicStore {
  topics: Topic[];
  loading: boolean;
  error: string | null;
  setTopics: (topics: Topic[]) => void;
  addTopic: (topic: Topic) => void;
  updateTopic: (id: string, topic: Partial<Topic>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useTopicStore = create<TopicStore>((set) => ({
  topics: [],
  loading: false,
  error: null,
  setTopics: (topics) => set({ topics }),
  addTopic: (topic) => set((state) => ({ topics: [...state.topics, topic] })),
  updateTopic: (id, updates) =>
    set((state) => ({
      topics: state.topics.map((t) => (t.id === id ? { ...t, ...updates } : t)),
    })),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));
