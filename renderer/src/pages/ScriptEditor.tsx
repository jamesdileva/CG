import { useState, useEffect } from 'react';
import { useTopicStore } from '../store/topicStore';
import { useScriptStore } from '../store/scriptStore';
import { apiClient } from '../api/client';
import './ScriptEditor.css';

export function ScriptEditor() {
  const { topics } = useTopicStore();
  const { scripts } = useScriptStore();
  const [selectedScriptId, setSelectedScriptId] = useState<string | null>(null);
  const [content, setContent] = useState('');
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [approving, setApproving] = useState(false);

  const selectedScript = selectedScriptId
    ? scripts.get(selectedScriptId)
    : Array.from(scripts.values())[0];

  useEffect(() => {
    if (selectedScript) {
      setSelectedScriptId(selectedScript.id);
      setContent(selectedScript.content || '');
      setIsDirty(false);
    }
  }, [selectedScript]);

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    setIsDirty(true);
  };

  const handleSave = async () => {
    if (!selectedScript) return;
    setSaving(true);
    try {
      await apiClient.updateScript(selectedScript.id, content, 'DRAFTED');
      setIsDirty(false);
    } catch (err) {
      console.error('Failed to save script:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedScript) return;
    setApproving(true);
    try {
      await apiClient.approveScript(selectedScript.id);
      // Update the script status in store
    } catch (err) {
      console.error('Failed to approve script:', err);
    } finally {
      setApproving(false);
    }
  };

  const availableScripts = Array.from(scripts.values());
  const scriptTopic = selectedScript
    ? topics.find((t) => t.id === selectedScript.topic_id)
    : null;

  return (
    <div className="script-editor">
      <div className="editor-header">
        <h1>Script Editor</h1>
        {scriptTopic && <h2>{scriptTopic.title}</h2>}
      </div>

      <div className="editor-container">
        <div className="script-list">
          <h3>Scripts</h3>
          {availableScripts.length === 0 ? (
            <p className="empty">No scripts yet. Generate one in Topics tab.</p>
          ) : (
            availableScripts.map((script) => {
              const topic = topics.find((t) => t.id === script.topic_id);
              return (
                <div
                  key={script.id}
                  className={`script-item ${
                    selectedScript?.id === script.id ? 'active' : ''
                  }`}
                  onClick={() => setSelectedScriptId(script.id)}
                >
                  <div className="script-item-title">{topic?.title}</div>
                  <div className="script-item-status">{script.status}</div>
                </div>
              );
            })
          )}
        </div>

        <div className="editor-main">
          {selectedScript ? (
            <>
              <div className="editor-toolbar">
                <button
                  onClick={handleSave}
                  disabled={!isDirty || saving}
                  className="btn btn-primary"
                >
                  {saving ? 'Saving...' : isDirty ? 'Save Changes' : 'Saved'}
                </button>
                <button
                  onClick={handleApprove}
                  disabled={approving || selectedScript.status === 'APPROVED'}
                  className="btn btn-success"
                >
                  {approving ? 'Approving...' : 'Approve Script'}
                </button>
                <span className="version">v{selectedScript.version}</span>
              </div>

              <textarea
                value={content}
                onChange={handleContentChange}
                className="script-textarea"
                placeholder="Script content will appear here..."
              />

              <div className="editor-info">
                <p>Status: {selectedScript.status}</p>
                <p>Created: {new Date(selectedScript.created_at).toLocaleString()}</p>
                {selectedScript.approved_at && (
                  <p>Approved: {new Date(selectedScript.approved_at).toLocaleString()}</p>
                )}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>No script selected. Generate a script from the Topics tab.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
