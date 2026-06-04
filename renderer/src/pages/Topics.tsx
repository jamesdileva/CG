import { useState, useEffect } from 'react';
import { useTopicStore } from '../store/topicStore';
import { useScriptStore } from '../store/scriptStore';
import { apiClient } from '../api/client';
import './Topics.css';

export function Topics() {
  const { topics, setTopics, setLoading, setError, updateTopic } = useTopicStore();
  const { setScript } = useScriptStore();
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [generatingScriptId, setGeneratingScriptId] = useState<string | null>(null);

  useEffect(() => {
    loadTopics();
  }, []);

  const loadTopics = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getTopics();
      setTopics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topics');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (topicId: string) => {
    setApprovingId(topicId);
    try {
      await apiClient.approveTopic(topicId);
      updateTopic(topicId, { status: 'APPROVED' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve topic');
    } finally {
      setApprovingId(null);
    }
  };

  const handleReject = async (topicId: string) => {
    try {
      await apiClient.rejectTopic(topicId);
      setTopics(topics.filter((t) => t.id !== topicId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject topic');
    }
  };

  const handleGenerateScript = async (topicId: string) => {
    setGeneratingScriptId(topicId);
    try {
      const result = await apiClient.generateScript(topicId);
      // Wait for script generation
      await new Promise((r) => setTimeout(r, 1500));
      const script = await apiClient.getScript(result.script_id);
      setScript(script);
      setSelectedTopic(topicId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate script');
    } finally {
      setGeneratingScriptId(null);
    }
  };

  const discoveredTopics = topics.filter((t) => t.status === 'DISCOVERED');
  const approvedTopics = topics.filter((t) => t.status === 'APPROVED');

  return (
    <div className="topics-container">
      <h1>Topics</h1>

      {discoveredTopics.length > 0 && (
        <div className="topics-section">
          <h2>Pending Review ({discoveredTopics.length})</h2>
          <div className="topics-grid">
            {discoveredTopics.map((topic) => (
              <div key={topic.id} className="topic-card">
                <div className="topic-header">
                  <h3>{topic.title}</h3>
                  <span className="status-badge">{topic.status}</span>
                </div>
                <p className="topic-description">{topic.description}</p>
                <div className="topic-actions">
                  <button
                    onClick={() => handleApprove(topic.id)}
                    disabled={approvingId === topic.id}
                    className="btn btn-success"
                  >
                    {approvingId === topic.id ? 'Approving...' : 'Approve'}
                  </button>
                  <button
                    onClick={() => handleReject(topic.id)}
                    className="btn btn-outline"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {approvedTopics.length > 0 && (
        <div className="topics-section">
          <h2>Approved ({approvedTopics.length})</h2>
          <div className="topics-grid">
            {approvedTopics.map((topic) => (
              <div key={topic.id} className="topic-card approved">
                <div className="topic-header">
                  <h3>{topic.title}</h3>
                  <span className="status-badge approved">APPROVED</span>
                </div>
                <p className="topic-description">{topic.description}</p>
                <button
                  onClick={() => handleGenerateScript(topic.id)}
                  disabled={generatingScriptId === topic.id}
                  className="btn btn-primary"
                >
                  {generatingScriptId === topic.id
                    ? 'Generating Script...'
                    : 'Generate Script'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {topics.length === 0 && (
        <div className="empty-state">
          <p>No topics yet. Go to Dashboard to generate topics.</p>
        </div>
      )}
    </div>
  );
}
