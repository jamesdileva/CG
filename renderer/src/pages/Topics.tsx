import { useState, useEffect, useRef } from 'react';
import { useTopicStore } from '../store/topicStore';
import { useScriptStore } from '../store/scriptStore';
import { apiClient } from '../api/client';
import './Topics.css';

export function Topics() {
  const { topics, setTopics, setLoading, setError, updateTopic } = useTopicStore();
  const { setScript } = useScriptStore();
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [researchingId, setResearchingId] = useState<string | null>(null);
  const [generatingScriptId, setGeneratingScriptId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    loadTopics();
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    if (researchingId || generatingScriptId) return;
    for (const t of topics) {
      if (t.status === 'RESEARCHING') {
        setResearchingId(t.id);
        startPollResearch(t.id);
      } else if (t.status === 'SCRIPT_DRAFTED' || t.status === 'SCRIPT_APPROVED') {
        // Could resume script poll if needed
      }
    }
  }, [topics.length > 0]);

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

  const startPollScript = async (topicId: string, scriptId: string) => {
    if (!mountedRef.current) return;
    try {
      const script = await apiClient.getScript(scriptId);
      if (script.status !== 'GENERATING' && script.content) {
        setScript(script);
        updateTopic(topicId, { status: 'SCRIPT_DRAFTED' });
        setGeneratingScriptId(null);
        return;
      }
    } catch {
      // continue polling
    }
    if (mountedRef.current) {
      setTimeout(() => startPollScript(topicId, scriptId), 2000);
    }
  };

  const handleGenerateScript = async (topicId: string) => {
    setGeneratingScriptId(topicId);
    try {
      const result = await apiClient.generateScript(topicId);
      startPollScript(topicId, result.script_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate script');
      setGeneratingScriptId(null);
    }
  };

  const handleDelete = async (topicId: string) => {
    setDeletingId(topicId);
    try {
      await apiClient.deleteTopic(topicId);
      setTopics(topics.filter((t) => t.id !== topicId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete topic');
    } finally {
      setDeletingId(null);
    }
  };

  const startPollResearch = async (topicId: string) => {
    if (!mountedRef.current) return;
    try {
      const status = await apiClient.getPipelineStatus(topicId);
      if (status.topic_status === 'RESEARCH_COMPLETE') {
        const updatedTopic = await apiClient.getTopic(topicId);
        updateTopic(topicId, { status: updatedTopic.status });
        setResearchingId(null);
        return;
      }
    } catch {
      // continue polling
    }
    if (mountedRef.current) {
      setTimeout(() => startPollResearch(topicId), 2000);
    }
  };

  const handleStartResearch = async (topicId: string) => {
    setResearchingId(topicId);
    try {
      await apiClient.startResearch(topicId);
      updateTopic(topicId, { status: 'RESEARCHING' });
      startPollResearch(topicId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start research');
      setResearchingId(null);
    }
  };

  const discoveredTopics = topics.filter((t) => t.status === 'DISCOVERED');
  const approvedTopics = topics.filter((t) =>
    ['APPROVED', 'RESEARCHING', 'RESEARCH_COMPLETE'].includes(t.status)
  );

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
                  <button
                    onClick={() => handleDelete(topic.id)}
                    disabled={deletingId === topic.id}
                    className="btn btn-outline btn-danger"
                  >
                    {deletingId === topic.id ? 'Deleting...' : 'Delete'}
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
                  <span className={`status-badge ${topic.status === 'APPROVED' ? 'approved' : ''}`}>
                    {topic.status === 'APPROVED' ? 'APPROVED' : topic.status.replace('_', ' ')}
                  </span>
                </div>
                <p className="topic-description">{topic.description}</p>
                <div className="topic-actions">
                  <button
                    onClick={() => handleStartResearch(topic.id)}
                    disabled={researchingId === topic.id}
                    className="btn btn-outline"
                  >
                    {researchingId === topic.id ? 'Researching...' : 'Run Research'}
                  </button>
                  <button
                    onClick={() => handleGenerateScript(topic.id)}
                    disabled={generatingScriptId === topic.id}
                    className="btn btn-primary"
                  >
                    {generatingScriptId === topic.id
                      ? 'Generating Script...'
                      : 'Generate Script'}
                  </button>
                  <button
                    onClick={() => handleDelete(topic.id)}
                    disabled={deletingId === topic.id}
                    className="btn btn-outline btn-danger"
                  >
                    {deletingId === topic.id ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
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
