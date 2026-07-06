import { useEffect, useState } from 'react';
import { useTopicStore } from '../store/topicStore';
import { apiClient } from '../api/client';
import './Dashboard.css';

interface AnalyticsSummary {
  total_topics: number;
  average_interest_score: number;
  top_topic: { id: string; title: string; interest_score: number } | null;
  total_analytics_ingests: number;
  total_views: number;
}

interface AnalyticsRow {
  id: string;
  video_id: string;
  views: number;
  likes: number;
  comments: number;
  topic_score: number;
  topic_title?: string;
  interest_score?: number;
  synced_at: string;
}

export function Dashboard() {
  const { setTopics, setError, topics } = useTopicStore();
  const [generating, setGenerating] = useState<Record<string, boolean>>({});
  const [topicCount, setTopicCount] = useState(5);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [recentAnalytics, setRecentAnalytics] = useState<AnalyticsRow[]>([]);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [rankings, analyticsData] = await Promise.all([
        apiClient.getAnalyticsRankings(),
        apiClient.listAnalytics(),
      ]);
      setSummary(rankings.summary);
      setRecentAnalytics(analyticsData.slice(0, 5));
    } catch {
      // rankings not available yet
    }
  };

  const handleGenerateTopics = async (style: string = 'default') => {
    setGenerating((prev) => ({ ...prev, [style]: true }));
    setError(null);
    try {
      await apiClient.generateTopics(topicCount, style);
      await new Promise((r) => setTimeout(r, 1000));
      const newTopics = await apiClient.getTopics();
      setTopics(newTopics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate topics');
    } finally {
      setGenerating((prev) => ({ ...prev, [style]: false }));
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>AI Documentary Studio</h1>
        <p>Generate, research, script, and produce documentaries</p>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h2>Generate Topics</h2>
          <p>Create up to 20 unique documentary topics</p>

          <div className="form-group">
            <label htmlFor="topic-count">Number of topics:</label>
            <input
              id="topic-count"
              type="number"
              min="1"
              max="20"
              value={topicCount}
              onChange={(e) => setTopicCount(parseInt(e.target.value))}
              disabled={Object.values(generating).some(Boolean)}
            />
          </div>

          <div className="style-buttons">
            <button
              onClick={() => handleGenerateTopics('default')}
              disabled={generating['default']}
              className="btn btn-primary"
            >
              {generating['default'] ? 'Generating...' : 'Standard'}
            </button>
            <button
              onClick={() => handleGenerateTopics('weird_history')}
              disabled={generating['weird_history']}
              className="btn btn-secondary"
            >
              {generating['weird_history'] ? 'Generating...' : 'Weird History'}
            </button>
            <button
              onClick={() => handleGenerateTopics('true_crime')}
              disabled={generating['true_crime']}
              className="btn btn-danger"
            >
              {generating['true_crime'] ? 'Generating...' : 'True Crime'}
            </button>
            <button
              onClick={() => handleGenerateTopics('mystery')}
              disabled={generating['mystery']}
              className="btn btn-accent"
            >
              {generating['mystery'] ? 'Generating...' : 'Mysteries'}
            </button>
          </div>
        </div>

        {topics.length > 0 && (
          <div className="dashboard-card">
            <h2>Pipeline Status</h2>
            <div className="stats">
              <div className="stat">
                <span className="stat-label">Total Topics</span>
                <span className="stat-value">{topics.length}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Approved</span>
                <span className="stat-value">
                  {topics.filter((t) => t.status === 'APPROVED').length}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Pending</span>
                <span className="stat-value">
                  {topics.filter((t) => t.status === 'DISCOVERED').length}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Rendered</span>
                <span className="stat-value">
                  {topics.filter((t) => t.status === 'VIDEO_RENDERED').length}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Uploaded</span>
                <span className="stat-value">
                  {topics.filter((t) => t.status === 'UPLOADED').length}
                </span>
              </div>
            </div>
          </div>
        )}

        {summary && (
          <div className="dashboard-card">
            <h2>Analytics Summary</h2>
            <div className="stats">
              <div className="stat">
                <span className="stat-label">Total Views</span>
                <span className="stat-value">{summary.total_views.toLocaleString()}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Avg Interest Score</span>
                <span className="stat-value">{summary.average_interest_score}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Ingests</span>
                <span className="stat-value">{summary.total_analytics_ingests}</span>
              </div>
              {summary.top_topic && (
                <div className="stat stat-wide">
                  <span className="stat-label">Top Topic</span>
                  <span className="stat-value">{summary.top_topic.title}</span>
                  <span className="stat-sub">Score: {summary.top_topic.interest_score}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {recentAnalytics.length > 0 && (
          <div className="dashboard-card">
            <h2>Recent Performance</h2>
            <div className="analytics-feed">
              {recentAnalytics.map((row) => (
                <div key={row.id} className="analytics-feed-item">
                  <span className="feed-title">{row.topic_title || row.video_id}</span>
                  <span className="feed-views">{row.views.toLocaleString()} views</span>
                  <span className="feed-score">Score: {row.topic_score}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="dashboard-card info">
        <h3>Next Steps</h3>
        <ol>
          <li>Generate topics above</li>
          <li>Go to Topics tab to review and approve</li>
          <li>Generate scripts for approved topics</li>
          <li>Edit and approve scripts</li>
          <li>Produce video in Production Studio</li>
          <li>Publish to YouTube</li>
        </ol>
      </div>
    </div>
  );
}
