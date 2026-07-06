import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { useTopicStore } from '../store/topicStore';
import { useScriptStore } from '../store/scriptStore';
import './Research.css';

interface ResearchSource {
  id: string;
  url: string | null;
  title: string | null;
  content: string | null;
  credibility_score: number;
}

interface ResearchFact {
  id: string;
  source_id: string | null;
  fact: string;
  confidence: number;
  verified: boolean;
}

interface TimelineItem {
  year: string;
  fact: string;
  source_id: string | null;
}

interface ResearchConflict {
  fact_a: { id: string; text: string };
  fact_b: { id: string; text: string };
  reason: string;
  year_a: string | null;
  year_b: string | null;
}

interface ResearchBundle {
  topic_id: string;
  sources: ResearchSource[];
  facts: ResearchFact[];
  timeline: TimelineItem[];
  conflicts: ResearchConflict[];
}

export function Research() {
  const { topics, setTopics, setError, updateTopic } = useTopicStore();
  const { setScript } = useScriptStore();
  const [selectedTopicId, setSelectedTopicId] = useState<string>('');
  const [bundle, setBundle] = useState<ResearchBundle | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [generatingScript, setGeneratingScript] = useState(false);
  const [editingFactId, setEditingFactId] = useState<string | null>(null);
  const [deletingSourceId, setDeletingSourceId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [manualOpen, setManualOpen] = useState(false);
  const [manualTitle, setManualTitle] = useState('');
  const [manualText, setManualText] = useState('');
  const [manualProcessing, setManualProcessing] = useState(false);

  const researchableTopics = topics.filter((topic) =>
    ['APPROVED', 'RESEARCHING', 'RESEARCH_COMPLETE', 'SCRIPT_DRAFTED'].includes(topic.status)
  );
  const selectedTopic = topics.find((topic) => topic.id === selectedTopicId);

  useEffect(() => {
    async function loadTopics() {
      try {
        const data = await apiClient.getTopics();
        setTopics(data);
        const firstResearchable = data.find((topic: { status: string }) =>
          ['APPROVED', 'RESEARCHING', 'RESEARCH_COMPLETE', 'SCRIPT_DRAFTED'].includes(topic.status)
        );
        if (firstResearchable && !selectedTopicId) {
          setSelectedTopicId(firstResearchable.id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load topics');
      }
    }

    loadTopics();
  }, []);

  useEffect(() => {
    if (selectedTopicId) {
      loadResearch(selectedTopicId);
      setBundle(null);
    }
  }, [selectedTopicId]);

  const loadResearch = async (topicId: string) => {
    setLoading(true);
    try {
      const data = await apiClient.getResearch(topicId);
      setBundle(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load research');
    } finally {
      setLoading(false);
    }
  };

  const runResearch = async () => {
    if (!selectedTopicId) return;

    const topicId = selectedTopicId;
    setRunning(true);
    try {
      await apiClient.startResearch(topicId);
      const poll = async () => {
        try {
          const status = await apiClient.getPipelineStatus(topicId);
          if (status.topic_status === 'RESEARCH_COMPLETE') {
            await loadResearch(topicId);
            const updatedTopic = await apiClient.getTopic(topicId);
            updateTopic(topicId, { status: updatedTopic.status });
            setRunning(false);
            return;
          }
          setTimeout(poll, 1500);
        } catch {
          setTimeout(poll, 1500);
        }
      };
      poll();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run research');
      setRunning(false);
    }
  };

  const handleGenerateScript = async (topicId: string) => {
    setGeneratingScript(true);
    try {
      const result = await apiClient.generateScript(topicId);
      const pollScript = async () => {
        try {
          const script = await apiClient.getScript(result.script_id);
          if (script.status !== 'GENERATING' && script.content) {
            setScript(script);
            updateTopic(topicId, { status: 'SCRIPT_DRAFTED' });
            setGeneratingScript(false);
            return;
          }
          setTimeout(pollScript, 2000);
        } catch {
          setTimeout(pollScript, 2000);
        }
      };
      pollScript();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate script');
      setGeneratingScript(false);
    }
  };

  const startEditFact = (factId: string, text: string) => {
    setEditingFactId(factId);
    setEditText(text);
  };

  const saveEditFact = async () => {
    if (!editingFactId || !editText.trim() || !bundle) return;
    const fact = bundle.facts.find((f) => f.id === editingFactId);
    if (!fact) return;
    setBundle({
      ...bundle,
      facts: bundle.facts.map((f) =>
        f.id === editingFactId ? { ...f, fact: editText.trim() } : f
      ),
    });
    setEditingFactId(null);
    setEditText('');
  };

  const cancelEditFact = () => {
    setEditingFactId(null);
    setEditText('');
  };

  const handleDeleteSource = async (sourceId: string) => {
    if (!bundle) return;
    setDeletingSourceId(sourceId);
    try {
      await apiClient.deleteResearchSource(sourceId);
      await loadResearch(bundle.topic_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete source');
    } finally {
      setDeletingSourceId(null);
    }
  };

  const handleManualSubmit = async () => {
    if (!manualTitle.trim() || !manualText.trim()) return;
    setManualProcessing(true);
    try {
      const result = await apiClient.submitManualResearch(manualTitle.trim(), manualText);
      // Reload topics and select the new one
      const newTopics = await apiClient.getTopics();
      setTopics(newTopics);
      setSelectedTopicId(result.topic_id);
      setBundle(result);
      setManualOpen(false);
      setManualTitle('');
      setManualText('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process manual input');
    } finally {
      setManualProcessing(false);
    }
  };

  return (
    <div className="research-page">
      <div className="manual-input-section">
        <button
          className="btn btn-outline manual-toggle"
          onClick={() => setManualOpen(!manualOpen)}
        >
          {manualOpen ? '−' : '+'} Manual Input
        </button>
        {manualOpen && (
          <div className="manual-input-form">
            <input
              type="text"
              placeholder="Article title"
              value={manualTitle}
              onChange={(e) => setManualTitle(e.target.value)}
              disabled={manualProcessing}
              className="manual-title-input"
            />
            <textarea
              placeholder="Paste the full article text here... (supports long articles, Wikipedia pages, etc.)"
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
              disabled={manualProcessing}
              rows={12}
              className="manual-text-input"
            />
            <button
              className="btn btn-primary"
              onClick={handleManualSubmit}
              disabled={manualProcessing || !manualTitle.trim() || !manualText.trim()}
            >
              {manualProcessing ? 'Processing...' : 'Process Text'}
            </button>
          </div>
        )}
      </div>

      <div className="research-header">
        <div>
          <h1>Research Viewer</h1>
          <p>Review sources, extracted facts, and timeline candidates before scripting.</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={runResearch}
          disabled={!selectedTopicId || running}
        >
          {running ? 'Researching...' : 'Run Research'}
        </button>
        {selectedTopic?.status === 'RESEARCH_COMPLETE' && (
          <button
            className="btn btn-success"
            onClick={() => handleGenerateScript(selectedTopicId)}
            disabled={generatingScript}
          >
            {generatingScript ? 'Generating Script...' : 'Generate Script'}
          </button>
        )}
      </div>

      <div className="research-toolbar">
        <label htmlFor="topic-select">Topic</label>
        <select
          id="topic-select"
          value={selectedTopicId}
          onChange={(event) => setSelectedTopicId(event.target.value)}
        >
          <option value="">Select an approved topic</option>
          {researchableTopics.map((topic) => (
            <option key={topic.id} value={topic.id}>
              {topic.title}
            </option>
          ))}
        </select>
        {selectedTopic && <span className="status-badge">{selectedTopic.status}</span>}
      </div>

      {!selectedTopicId && (
        <div className="empty-state">
          <p>Approve a topic first, then run research from this page.</p>
        </div>
      )}

      {selectedTopicId && loading && <div className="empty-state">Loading research...</div>}

      {selectedTopicId && !loading && bundle && (
        <>
          {bundle.conflicts.length > 0 && (
            <section className="research-panel conflicts-panel">
              <h2>Conflicts ({bundle.conflicts.length})</h2>
              <div className="conflicts-list">
                {bundle.conflicts.map((conflict, index) => (
                  <article key={index} className="conflict-item">
                    <div className="conflict-reason">Contradiction: {conflict.reason}</div>
                    <div className="conflict-facts">
                      <div className="conflict-fact">
                        <span className="conflict-year">{conflict.year_a && `(${conflict.year_a})`}</span>
                        {conflict.fact_a.text}
                      </div>
                      <div className="conflict-vs">vs</div>
                      <div className="conflict-fact">
                        <span className="conflict-year">{conflict.year_b && `(${conflict.year_b})`}</span>
                        {conflict.fact_b.text}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}

          <div className="research-grid">
            <section className="research-panel sources-panel">
              <h2>Sources ({bundle.sources.length})</h2>
              {bundle.sources.length === 0 ? (
                <p className="muted">No sources saved yet.</p>
              ) : (
                bundle.sources.map((source) => (
                  <article key={source.id} className="source-item">
                    <div className="source-title-row">
                      <span className="source-title">{source.title || 'Untitled source'}</span>
                      <button
                        className="btn btn-small btn-danger"
                        onClick={() => handleDeleteSource(source.id)}
                        disabled={deletingSourceId === source.id}
                      >
                        {deletingSourceId === source.id ? '...' : 'Delete'}
                      </button>
                    </div>
                    <div className="source-meta">
                      <span>{Math.round(source.credibility_score * 100)}% credibility</span>
                      {source.url && <span>{source.url}</span>}
                    </div>
                    <p>{source.content?.slice(0, 320)}</p>
                  </article>
                ))
              )}
            </section>

            <section className="research-panel">
              <h2>Facts ({bundle.facts.length})</h2>
              {bundle.facts.length === 0 ? (
                <p className="muted">No facts extracted yet.</p>
              ) : (
                bundle.facts.map((fact) => (
                  <article key={fact.id} className="fact-item">
                    {editingFactId === fact.id ? (
                      <div className="fact-edit">
                        <textarea
                          value={editText}
                          onChange={(e) => setEditText(e.target.value)}
                          className="fact-edit-input"
                          rows={3}
                        />
                        <div className="fact-edit-actions">
                          <button className="btn btn-small btn-primary" onClick={saveEditFact}>
                            Save
                          </button>
                          <button className="btn btn-small btn-outline" onClick={cancelEditFact}>
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <p onClick={() => startEditFact(fact.id, fact.fact)} className="fact-text">
                          {fact.fact}
                        </p>
                        <span className="fact-meta">
                          {Math.round(fact.confidence * 100)}% confidence
                          {fact.verified && <span className="verified-badge">Verified</span>}
                        </span>
                      </>
                    )}
                  </article>
                ))
              )}
            </section>

            <section className="research-panel">
              <h2>Timeline ({bundle.timeline.length})</h2>
              {bundle.timeline.length === 0 ? (
                <p className="muted">No dated facts found yet.</p>
              ) : (
                bundle.timeline.map((item, index) => (
                  <article key={`${item.year}-${index}`} className="timeline-item">
                    <strong>{item.year}</strong>
                    <p>{item.fact}</p>
                  </article>
                ))
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
