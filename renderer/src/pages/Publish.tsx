import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { useTopicStore } from '../store/topicStore';
import './Publish.css';

interface VideoBundle {
  topic_id: string;
  video: {
    id: string;
    status: string;
    file_path: string | null;
  } | null;
}

interface Upload {
  id: string;
  video_id: string;
  youtube_id: string | null;
  title: string | null;
  description: string | null;
  tags: string | null;
  status: string;
  scheduled_at: string | null;
  uploaded_at: string | null;
}

export function Publish() {
  const { topics, setTopics, setError } = useTopicStore();
  const [selectedTopicId, setSelectedTopicId] = useState('');
  const [videoBundle, setVideoBundle] = useState<VideoBundle | null>(null);
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [selectedUploadId, setSelectedUploadId] = useState('');
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [authenticated, setAuthenticated] = useState(false);

  const [uploadResult, setUploadResult] = useState<{ youtube_id: string; youtube_url: string } | null>(null);

  const renderedTopics = topics.filter((topic) =>
    ['VIDEO_RENDERED', 'READY_TO_UPLOAD', 'UPLOADED', 'ANALYTICS_COLLECTED'].includes(topic.status)
  );
  const selectedUpload = uploads.find((upload) => upload.id === selectedUploadId) || uploads[0];

  useEffect(() => {
    async function load() {
      try {
        const [topicData, uploadData, authData] = await Promise.all([
          apiClient.getTopics(),
          apiClient.getUploads(),
          apiClient.getAuthStatus(),
        ]);
        setTopics(topicData);
        setUploads(uploadData);
        setAuthenticated(authData.authenticated);
        const first = topicData.find((topic: { status: string }) =>
          ['VIDEO_RENDERED', 'READY_TO_UPLOAD', 'UPLOADED', 'ANALYTICS_COLLECTED'].includes(topic.status)
        );
        if (first && !selectedTopicId) {
          setSelectedTopicId(first.id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load publish data');
      }
    }

    load();
  }, []);

  useEffect(() => {
    if (selectedTopicId) {
      loadVideo(selectedTopicId);
    }
  }, [selectedTopicId]);

  const loadVideo = async (topicId: string) => {
    const data = await apiClient.getVideo(topicId);
    setVideoBundle(data);
  };

  const refreshUploads = useCallback(async () => {
    const data = await apiClient.getUploads();
    setUploads(data);
    if (data.length > 0 && !selectedUploadId) {
      setSelectedUploadId(data[0].id);
    }
  }, []);

  useEffect(() => {
    if (selectedUploadId) {
      setUploadResult(null);
    }
  }, [selectedUploadId]);

  const buildMetadata = async () => {
    if (!videoBundle?.video) return;
    setBusy(true);
    try {
      const upload = await apiClient.buildPublishMetadata(videoBundle.video.id);
      await refreshUploads();
      setSelectedUploadId(upload.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to build metadata');
    } finally {
      setBusy(false);
    }
  };

  const handleAuth = async () => {
    try {
      setBusy(true);
      const data = await apiClient.getAuthUrl();
      const code = await window.electron.openAuthWindow(data.auth_url);
      await apiClient.exchangeAuthCode(code);
      setAuthenticated(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get auth URL');
    } finally {
      setBusy(false);
    }
  };

  const approve = async () => {
    if (!selectedUpload) return;
    setBusy(true);
    try {
      await apiClient.approveUpload(selectedUpload.id);
      await refreshUploads();
      if (selectedTopicId) {
        const updatedTopic = await apiClient.getTopic(selectedTopicId);
        setTopics(topics.map((topic) => (topic.id === selectedTopicId ? updatedTopic : topic)));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve upload');
    } finally {
      setBusy(false);
    }
  };

  const uploadToYouTube = async () => {
    if (!selectedUpload) return;
    setBusy(true);
    setUploading(true);
    setUploadProgress('Starting upload...');
    setUploadResult(null);
    try {
      const { job_id } = await apiClient.uploadToYouTube(selectedUpload.id);
      const poll = setInterval(async () => {
        const job = await apiClient.getJobStatus(job_id);
        if (!job) return;
        setUploadProgress(job.status);
        if (job.status === 'COMPLETE') {
          clearInterval(poll);
          setUploadResult({ youtube_id: job.result?.youtube_id, youtube_url: `https://youtu.be/${job.result?.youtube_id}` });
          setUploading(false);
          setBusy(false);
          await refreshUploads();
          if (selectedTopicId) {
            const updatedTopic = await apiClient.getTopic(selectedTopicId);
            setTopics(topics.map((topic) => (topic.id === selectedTopicId ? updatedTopic : topic)));
          }
        } else if (job.status === 'FAILED') {
          clearInterval(poll);
          setError(job.error || 'YouTube upload failed');
          setUploading(false);
          setBusy(false);
        }
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'YouTube upload failed');
      setUploading(false);
      setBusy(false);
    }
  };

  const mockUpload = async () => {
    if (!selectedUpload) return;
    setBusy(true);
    try {
      const result = await apiClient.mockUpload(selectedUpload.id);
      setUploadResult({ youtube_id: result.youtube_id, youtube_url: `https://youtu.be/${result.youtube_id}` });
      await refreshUploads();
      if (selectedTopicId) {
        const updatedTopic = await apiClient.getTopic(selectedTopicId);
        setTopics(topics.map((topic) => (topic.id === selectedTopicId ? updatedTopic : topic)));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to mock upload');
    } finally {
      setBusy(false);
    }
  };

  const isReady = selectedUpload?.status === 'READY_TO_UPLOAD';
  const isUploaded = selectedUpload?.status === 'UPLOADED';

  return (
    <div className="publish-page">
      <div className="publish-header">
        <div>
          <h1>Publish Manager</h1>
          <p>Build metadata, authenticate with YouTube, approve, and upload.</p>
        </div>
        <div className="publish-actions">
          <button className="btn btn-primary" onClick={buildMetadata} disabled={!videoBundle?.video || busy}>
            Build Metadata
          </button>
        </div>
      </div>

      <div className="publish-auth-bar">
        <span className="auth-label">YouTube</span>
        {authenticated ? (
          <span className="status-badge status-ok">Authenticated</span>
        ) : (
          <>
            <span className="status-badge status-missing">Not authenticated</span>
            <button className="btn btn-outline btn-sm" onClick={handleAuth}>
              Sign in
            </button>

          </>
        )}
      </div>

      <div className="publish-toolbar">
        <label htmlFor="publish-topic">Topic</label>
        <select
          id="publish-topic"
          value={selectedTopicId}
          onChange={(event) => setSelectedTopicId(event.target.value)}
        >
          <option value="">Select rendered video</option>
          {renderedTopics.map((topic) => (
            <option key={topic.id} value={topic.id}>
              {topic.title}
            </option>
          ))}
        </select>
      </div>

      {!videoBundle?.video && (
        <div className="empty-state">
          <p>Render a video in Production before building publish metadata.</p>
        </div>
      )}

      {videoBundle?.video && (
        <div className="publish-grid">
          <section className="publish-panel">
            <h2>Rendered Video</h2>
            <p className="file-path">{videoBundle.video.file_path}</p>
            <p className="muted">Video ID: {videoBundle.video.id}</p>
          </section>

          <section className="publish-panel">
            <h2>Upload Records</h2>
            {uploads.length === 0 ? (
              <p className="muted">No publish metadata yet.</p>
            ) : (
              <>
                <select
                  value={selectedUpload?.id || ''}
                  onChange={(event) => setSelectedUploadId(event.target.value)}
                >
                  {uploads.map((upload) => (
                    <option key={upload.id} value={upload.id}>
                      {upload.title || upload.id} - {upload.status}
                    </option>
                  ))}
                </select>

                {selectedUpload && (
                  <article className="upload-card">
                    <span className="status-badge">{selectedUpload.status}</span>
                    <h3>{selectedUpload.title}</h3>
                    <p>{selectedUpload.description}</p>
                    <p className="muted">Tags: {selectedUpload.tags}</p>
                    {selectedUpload.youtube_id && (
                      <p className="muted">YouTube ID: {selectedUpload.youtube_id}</p>
                    )}

                    {uploadResult && (
                      <div className="upload-result">
                        <p>
                          Uploaded:{' '}
                          <a href={uploadResult.youtube_url} target="_blank" rel="noreferrer">
                            {uploadResult.youtube_url}
                          </a>
                        </p>
                      </div>
                    )}

                    <div className="publish-actions">
                      {!isUploaded && (
                        <button className="btn btn-outline" onClick={approve} disabled={busy || isUploaded}>
                          Approve
                        </button>
                      )}
                      {isReady && authenticated && (
                        <button className="btn btn-success" onClick={uploadToYouTube} disabled={busy || uploading}>
                          {uploading ? `Uploading (${uploadProgress})...` : 'Upload to YouTube'}
                        </button>
                      )}
                      {isReady && !authenticated && (
                        <p className="muted">Sign in with YouTube above to enable upload.</p>
                      )}
                      <button className="btn btn-outline" onClick={mockUpload} disabled={busy}>
                        Mock Upload
                      </button>
                    </div>
                  </article>
                )}
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
