const API_BASE = 'http://127.0.0.1:8000/api';

export const apiClient = {
  async generateTopics(count: number = 5) {
    const res = await fetch(`${API_BASE}/topics/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_topics: count }),
    });
    return res.json();
  },

  async getTopics(status?: string, limit: number = 50) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());

    const res = await fetch(`${API_BASE}/topics?${params}`);
    return res.json();
  },

  async getTopic(id: string) {
    const res = await fetch(`${API_BASE}/topics/${id}`);
    return res.json();
  },

  async approveTopic(id: string) {
    const res = await fetch(`${API_BASE}/topics/${id}/approve`, {
      method: 'POST',
    });
    return res.json();
  },

  async rejectTopic(id: string) {
    const res = await fetch(`${API_BASE}/topics/${id}/reject`, {
      method: 'POST',
    });
    return res.json();
  },

  async generateScript(topicId: string) {
    const res = await fetch(`${API_BASE}/scripts/${topicId}/generate`, {
      method: 'POST',
    });
    return res.json();
  },

  async getScript(id: string) {
    const res = await fetch(`${API_BASE}/scripts/${id}`);
    return res.json();
  },

  async getTopicScripts(topicId: string) {
    const res = await fetch(`${API_BASE}/scripts/topic/${topicId}`);
    return res.json();
  },

  async updateScript(id: string, content: string, status?: string) {
    const res = await fetch(`${API_BASE}/scripts/${id}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, status }),
    });
    return res.json();
  },

  async approveScript(id: string) {
    const res = await fetch(`${API_BASE}/scripts/${id}/approve`, {
      method: 'POST',
    });
    return res.json();
  },

  async getPipelineStatus(topicId: string) {
    const res = await fetch(`${API_BASE}/pipeline/status/${topicId}`);
    return res.json();
  },
};
