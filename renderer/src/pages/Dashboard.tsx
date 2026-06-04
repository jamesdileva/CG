import { useState } from 'react';
import { useTopicStore } from '../store/topicStore';
import { apiClient } from '../api/client';
import './Dashboard.css';

export function Dashboard() {
  const { setTopics, setLoading, setError, topics } = useTopicStore();
  const [generating, setGenerating] = useState(false);
  const [topicCount, setTopicCount] = useState(5);

  const handleGenerateTopics = async () => {
    setGenerating(true);
    setError(null);
    try {
      await apiClient.generateTopics(topicCount);
      // Wait a moment then fetch topics
      await new Promise((r) => setTimeout(r, 1000));
      const newTopics = await apiClient.getTopics();
      setTopics(newTopics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate topics');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>AI Documentary Studio</h1>
        <p>Generate, research, script, and produce documentaries</p>
      </div>

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
            disabled={generating}
          />
        </div>

        <button
          onClick={handleGenerateTopics}
          disabled={generating}
          className="btn btn-primary"
        >
          {generating ? 'Generating...' : 'Generate Topics'}
        </button>
      </div>

      {topics.length > 0 && (
        <div className="dashboard-card">
          <h2>Status</h2>
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
          </div>
        </div>
      )}

      <div className="dashboard-card info">
        <h3>Next Steps</h3>
        <ol>
          <li>Generate topics above</li>
          <li>Go to Topics tab to review and approve</li>
          <li>Generate scripts for approved topics</li>
          <li>Edit and approve scripts</li>
        </ol>
      </div>
    </div>
  );
}
