const API_BASE = 'http://127.0.0.1:8000/api';

export const apiClient = {
  async generateTopics(count: number = 5, style: string = 'default') {
    const res = await fetch(`${API_BASE}/topics/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_topics: count, style }),
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

  async deleteTopic(id: string) {
    const res = await fetch(`${API_BASE}/topics/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`Delete failed: ${res.statusText}`);
    return res.json();
  },

  async generateScript(topicId: string) {
    const res = await fetch(`${API_BASE}/scripts/${topicId}/generate`, {
      method: 'POST',
    });
    return res.json();
  },

  async startResearch(topicId: string, maxSources: number = 8) {
    const res = await fetch(
      `${API_BASE}/research/start/${topicId}?max_sources=${maxSources}`,
      { method: 'POST' }
    );
    return res.json();
  },

  async getResearch(topicId: string) {
    const res = await fetch(`${API_BASE}/research/${topicId}`);
    return res.json();
  },

  async deleteResearchSource(sourceId: string) {
    const res = await fetch(`${API_BASE}/research/source/${sourceId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Delete source failed: ${res.statusText}`);
    return res.json();
  },

  async renderVideo(topicId: string) {
    const res = await fetch(`${API_BASE}/videos/render/${topicId}`, {
      method: 'POST',
    });
    return res.json();
  },

  async getVideo(topicId: string) {
    const res = await fetch(`${API_BASE}/videos/${topicId}`);
    return res.json();
  },

  async buildPublishMetadata(videoId: string) {
    const res = await fetch(`${API_BASE}/publish/metadata`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_id: videoId }),
    });
    return res.json();
  },

  async getAnalyticsRankings() {
    const res = await fetch(`${API_BASE}/analytics/rankings`);
    return res.json();
  },

  async pullAnalytics() {
    const res = await fetch(`${API_BASE}/analytics/pull`, { method: 'POST' });
    return res.json();
  },

  async getUploads(status?: string) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/publish${suffix}`);
    return res.json();
  },

  async updateUpload(
    uploadId: string,
    payload: { title?: string; description?: string; tags?: string[]; scheduled_at?: string }
  ) {
    const res = await fetch(`${API_BASE}/publish/${uploadId}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  async approveUpload(uploadId: string) {
    const res = await fetch(`${API_BASE}/publish/${uploadId}/approve`, {
      method: 'POST',
    });
    return res.json();
  },

  async mockUpload(uploadId: string) {
    const res = await fetch(`${API_BASE}/publish/${uploadId}/mock-upload`, {
      method: 'POST',
    });
    return res.json();
  },

  async ingestAnalytics(payload: {
    video_id: string;
    youtube_id?: string;
    views: number;
    likes: number;
    comments: number;
    watch_time_seconds: number;
    click_through_rate: number;
  }) {
    const res = await fetch(`${API_BASE}/analytics/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  async getAnalytics(videoId: string) {
    const res = await fetch(`${API_BASE}/analytics/${videoId}`);
    return res.json();
  },

  async listAnalytics() {
    const res = await fetch(`${API_BASE}/analytics`);
    return res.json();
  },

  async listScripts() {
    const res = await fetch(`${API_BASE}/scripts`);
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

  async submitManualResearch(title: string, text: string) {
    const res = await fetch(`${API_BASE}/research/manual-input`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, text }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getPipelineStatus(topicId: string) {
    const res = await fetch(`${API_BASE}/pipeline/status/${topicId}`);
    return res.json();
  },

  // Phase 3: Video Pipeline
  async generateTTS(topicId: string, rate: string = '+0%', voice: string = '') {
    const params = new URLSearchParams({ rate });
    if (voice) params.append('voice', voice);
    const res = await fetch(`${API_BASE}/videos/tts/${topicId}?${params}`, { method: 'POST' });
    return res.json();
  },

  async getTTSStatus(topicId: string) {
    const res = await fetch(`${API_BASE}/videos/tts/${topicId}`);
    return res.json();
  },

  async extractImages(topicId: string) {
    const res = await fetch(`${API_BASE}/videos/images/${topicId}`, { method: 'POST' });
    return res.json();
  },

  async getAssets(topicId: string, assetType?: string) {
    const suffix = assetType ? `?asset_type=${assetType}` : '';
    const res = await fetch(`${API_BASE}/videos/assets/${topicId}${suffix}`);
    return res.json();
  },

  async generateThumbnail(topicId: string) {
    const res = await fetch(`${API_BASE}/videos/thumbnail/${topicId}`, { method: 'POST' });
    return res.json();
  },

  // Phase 4: YouTube Integration
  async getAuthStatus() {
    const res = await fetch(`${API_BASE}/publish/auth/status`);
    return res.json();
  },

  async getAuthUrl() {
    const res = await fetch(`${API_BASE}/publish/auth/url`);
    return res.json();
  },

  async exchangeAuthCode(code: string) {
    const res = await fetch(`${API_BASE}/publish/auth/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    return res.json();
  },

  async uploadToYouTube(uploadId: string) {
    const res = await fetch(`${API_BASE}/publish/${uploadId}/upload-to-youtube`, {
      method: 'POST',
    });
    return res.json();
  },

  async getJobStatus(jobId: string) {
    const res = await fetch(`${API_BASE}/pipeline/jobs/${jobId}`);
    if (!res.ok) return null;
    return res.json();
  },
};
