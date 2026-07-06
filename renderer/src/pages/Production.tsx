import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { useTopicStore } from '../store/topicStore';
import './Production.css';

interface Scene {
  id: string;
  order_index: number;
  text: string;
  duration: number;
  audio_path: string | null;
  image_path: string | null;
}

interface Video {
  id: string;
  status: string;
  file_path: string | null;
  duration_seconds: number | null;
  file_size_bytes: number | null;
}

interface VideoBundle {
  topic_id: string;
  video: Video | null;
  scenes: Scene[];
}

interface Asset {
  id: string;
  type: string;
  file_path: string;
  topic_id: string;
  scene_id: string | null;
  source_url: string | null;
}

export function Production() {
  const { topics, setTopics, setError } = useTopicStore();
  const [selectedTopicId, setSelectedTopicId] = useState('');
  const [bundle, setBundle] = useState<VideoBundle | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [ttsRate, setTtsRate] = useState('+0%');
  const [ttsVoice, setTtsVoice] = useState('');
  const [assets, setAssets] = useState<Asset[]>([]);
  const [generatingThumb, setGeneratingThumb] = useState(false);

  const renderableTopics = topics.filter((topic) =>
    ['SCRIPT_DRAFTED', 'SCRIPT_APPROVED', 'VIDEO_RENDERED'].includes(topic.status)
  );
  const selectedTopic = topics.find((topic) => topic.id === selectedTopicId);

  const loadTopics = useCallback(async () => {
    try {
      const data = await apiClient.getTopics();
      setTopics(data);
      const firstRenderable = data.find((topic: { status: string }) =>
        ['SCRIPT_DRAFTED', 'SCRIPT_APPROVED', 'VIDEO_RENDERED'].includes(topic.status)
      );
      if (firstRenderable && !selectedTopicId) {
        setSelectedTopicId(firstRenderable.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topics');
    }
  }, []);

  useEffect(() => {
    loadTopics();
  }, [loadTopics]);

  useEffect(() => {
    if (selectedTopicId) {
      loadVideo(selectedTopicId);
      loadAssets(selectedTopicId);
    }
  }, [selectedTopicId]);

  const loadVideo = async (topicId: string) => {
    setLoading(true);
    try {
      const data = await apiClient.getVideo(topicId);
      setBundle(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load video status');
    } finally {
      setLoading(false);
    }
  };

  const loadAssets = async (topicId: string) => {
    try {
      const data = await apiClient.getAssets(topicId);
      setAssets(data.assets || []);
    } catch {
      // assets not available yet
    }
  };

  const handleGenerate = async () => {
    if (!selectedTopicId) return;
    setGenerating(true);
    setError(null);
    const topicId = selectedTopicId;
    try {
      // Step 1: TTS
      await apiClient.generateTTS(topicId, ttsRate, ttsVoice);
      await new Promise<void>((resolve) => {
        const poll = async () => {
          try {
            const status = await apiClient.getTTSStatus(topicId);
            if (status.scenes.length > 0 && status.scenes.every((s: { has_audio: boolean }) => s.has_audio)) {
              await loadVideo(topicId);
              await loadAssets(topicId);
              resolve();
              return;
            }
          } catch { /* continue */ }
          setTimeout(poll, 2000);
        };
        setTimeout(poll, 2000);
      });

      // Step 2: Render
      await apiClient.renderVideo(topicId);
      await new Promise<void>((resolve) => {
        const poll = async () => {
          try {
            const video = await apiClient.getVideo(topicId);
            if (video.video?.status === 'RENDERED') {
              await loadVideo(topicId);
              const updated = await apiClient.getTopic(topicId);
              setTopics(topics.map((t) => (t.id === topicId ? updated : t)));
              resolve();
              return;
            }
          } catch { /* continue */ }
          setTimeout(poll, 2000);
        };
        setTimeout(poll, 3000);
      });

      // Step 3: Extract images
      await apiClient.extractImages(topicId);
      await new Promise<void>((resolve) => {
        let attempts = 0;
        let initialCount: number | null = null;
        const poll = async () => {
          attempts++;
          if (attempts > 60) { resolve(); return; }
          try {
            const fresh = await apiClient.getAssets(topicId);
            const freshImages = (fresh.assets || []).filter((a: Asset) => a.type === 'image');
            if (initialCount === null) initialCount = freshImages.length;
            if (initialCount !== null && freshImages.length > initialCount) {
              setAssets(fresh.assets || []);
              resolve();
              return;
            }
          } catch { /* continue */ }
          setTimeout(poll, 2000);
        };
        setTimeout(poll, 2000);
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateThumbnail = async () => {
    if (!selectedTopicId) return;
    setGeneratingThumb(true);
    try {
      await apiClient.generateThumbnail(selectedTopicId);
      await loadAssets(selectedTopicId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate thumbnail');
    } finally {
      setGeneratingThumb(false);
    }
  };

  const audioAssets = assets.filter((a) => a.type === 'audio');
  const imageAssets = assets.filter((a) => a.type === 'image');
  const thumbnailAssets = assets.filter((a) => a.type === 'thumbnail');

  return (
    <div className="production-page">
      <div className="production-header">
        <div>
          <h1>Production Studio</h1>
          <p>Generate audio, extract images, then render a local MVP MP4.</p>
        </div>
        <div className="production-actions">
          <label className="rate-label">
            Voice:
            <select value={ttsVoice} onChange={(e) => setTtsVoice(e.target.value)} className="rate-select">
              <option value="">Jenny (US Female)</option>
              <option value="en-US-GuyNeural">Guy (US Male)</option>
              <option value="en-US-AriaNeural">Aria (US Female)</option>
              <option value="en-GB-SoniaNeural">Sonia (UK Female)</option>
              <option value="en-GB-RyanNeural">Ryan (UK Male)</option>
              <option value="en-AU-NatashaNeural">Natasha (AU Female)</option>
            </select>
          </label>
          <label className="rate-label">
            Rate:
            <select value={ttsRate} onChange={(e) => setTtsRate(e.target.value)} className="rate-select">
              <option value="-30%">Slow (-30%)</option>
              <option value="-15%">Slower (-15%)</option>
              <option value="+0%">Normal</option>
              <option value="+15%">Faster (+15%)</option>
              <option value="+30%">Fast (+30%)</option>
            </select>
          </label>
          <button
            className="btn btn-primary"
            onClick={handleGenerate}
            disabled={!selectedTopicId || generating || !bundle?.scenes?.length}
          >
            {generating ? 'Generating...' : 'Generate Documentary'}
          </button>
          {generating && <span className="generating-hint">TTS → Render → Images</span>}
        </div>
      </div>

      <div className="production-toolbar">
        <label htmlFor="production-topic">Topic</label>
        <select
          id="production-topic"
          value={selectedTopicId}
          onChange={(event) => setSelectedTopicId(event.target.value)}
        >
          <option value="">Select a scripted topic</option>
          {renderableTopics.map((topic) => (
            <option key={topic.id} value={topic.id}>
              {topic.title}
            </option>
          ))}
        </select>
        {selectedTopic && <span className="status-badge">{selectedTopic.status}</span>}
      </div>

      {!selectedTopicId && (
        <div className="empty-state">
          <p>Generate a script first, then return here to produce the video.</p>
        </div>
      )}

      {selectedTopicId && loading && <div className="empty-state">Loading production status...</div>}

      {selectedTopicId && !loading && bundle && (
        <div className="production-grid">
          <section className="production-panel">
            <h2>Video</h2>
            {bundle.video ? (
              <div className="video-summary">
                <div>
                  <span>Status</span>
                  <strong>{bundle.video.status}</strong>
                </div>
                <div>
                  <span>Duration</span>
                  <strong>{bundle.video.duration_seconds || 0}s</strong>
                </div>
                <div>
                  <span>Size</span>
                  <strong>
                    {bundle.video.file_size_bytes
                      ? `${Math.round(bundle.video.file_size_bytes / 1024)} KB`
                      : 'Pending'}
                  </strong>
                </div>
                {bundle.video.file_path && (
                  <p className="file-path">{bundle.video.file_path}</p>
                )}
                {bundle.video.status === 'RENDERED' && (
                  <button
                    className="btn btn-outline"
                    onClick={handleGenerateThumbnail}
                    disabled={generatingThumb}
                    style={{ marginTop: 12 }}
                  >
                    {generatingThumb ? 'Generating...' : 'Generate Thumbnail'}
                  </button>
                )}
              </div>
            ) : (
              <p className="muted">No render yet.</p>
            )}

            {thumbnailAssets.length > 0 && (
              <div className="asset-section">
                <h3>Thumbnails</h3>
                {thumbnailAssets.map((asset) => (
                  <p key={asset.id} className="file-path">{asset.file_path}</p>
                ))}
              </div>
            )}
          </section>

          <section className="production-panel">
            <h2>Scenes ({bundle.scenes.length})</h2>
            {bundle.scenes.length === 0 ? (
              <p className="muted">Render once to generate scene records.</p>
            ) : (
              bundle.scenes.map((scene) => (
                <article key={scene.id} className="scene-item">
                  <div className="scene-header">
                    <strong>Scene {scene.order_index + 1}</strong>
                    <span>{Math.round(scene.duration)}s</span>
                    {scene.audio_path && <span className="status-badge status-ok">Audio</span>}
                  </div>
                  <p>{scene.text}</p>
                </article>
              ))
            )}

            {audioAssets.length > 0 && (
              <div className="asset-section">
                <h3>Audio Files ({audioAssets.length})</h3>
                {audioAssets.map((asset) => (
                  <p key={asset.id} className="file-path">{asset.file_path}</p>
                ))}
              </div>
            )}

            {imageAssets.length > 0 && (
              <div className="asset-section">
                <h3>Images ({imageAssets.length})</h3>
                <div className="image-grid">
                  {imageAssets.map((asset) => {
                    const filename = asset.file_path.split('\\').pop()?.split('/').pop() || '';
                    return (
                    <div key={asset.id} className="image-thumb">
                      <img
                        src={`http://127.0.0.1:8000/api/videos/asset-file/${asset.topic_id}/${filename}`}
                        alt=""
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                      {asset.source_url && (
                        <a
                          href={asset.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="image-source"
                          title={asset.source_url}
                        >
                          source
                        </a>
                      )}
                    </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}



