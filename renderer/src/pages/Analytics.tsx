import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import './Analytics.css';

interface Upload {
  id: string;
  video_id: string;
  youtube_id: string | null;
  title: string | null;
  status: string;
}

interface AnalyticsRow {
  id: string;
  video_id: string;
  youtube_id: string | null;
  views: number;
  likes: number;
  comments: number;
  watch_time_seconds: number;
  click_through_rate: number;
  topic_score: number;
  synced_at: string;
  topic_title?: string;
}

export function Analytics() {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [rows, setRows] = useState<AnalyticsRow[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState('');
  const [views, setViews] = useState(1000);
  const [likes, setLikes] = useState(50);
  const [comments, setComments] = useState(8);
  const [watchTime, setWatchTime] = useState(240000);
  const [ctr, setCtr] = useState(5.2);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    const [uploadData, analyticsData] = await Promise.all([
      apiClient.getUploads(),
      apiClient.listAnalytics(),
    ]);
    setUploads(uploadData);
    setRows(analyticsData);
    const firstUploaded = uploadData.find((upload: Upload) => upload.status === 'UPLOADED');
    if (firstUploaded && !selectedVideoId) {
      setSelectedVideoId(firstUploaded.video_id);
    }
  };

  const ingest = async () => {
    const upload = uploads.find((item) => item.video_id === selectedVideoId);
    if (!selectedVideoId) return;

    setBusy(true);
    try {
      await apiClient.ingestAnalytics({
        video_id: selectedVideoId,
        youtube_id: upload?.youtube_id || undefined,
        views,
        likes,
        comments,
        watch_time_seconds: watchTime,
        click_through_rate: ctr,
      });
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div>
          <h1>Analytics</h1>
          <p>Capture performance metrics and feed a topic score back into the pipeline.</p>
        </div>
        <button className="btn btn-primary" onClick={ingest} disabled={!selectedVideoId || busy}>
          Ingest Metrics
        </button>
      </div>

      <section className="analytics-panel">
        <h2>Manual Ingestion</h2>
        <div className="analytics-form">
          <label>
            Video
            <select value={selectedVideoId} onChange={(event) => setSelectedVideoId(event.target.value)}>
              <option value="">Select uploaded video</option>
              {uploads
                .filter((upload) => upload.status === 'UPLOADED')
                .map((upload) => (
                  <option key={upload.id} value={upload.video_id}>
                    {upload.title || upload.video_id}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Views
            <input type="number" min="0" value={views} onChange={(event) => setViews(Number(event.target.value))} />
          </label>
          <label>
            Likes
            <input type="number" min="0" value={likes} onChange={(event) => setLikes(Number(event.target.value))} />
          </label>
          <label>
            Comments
            <input type="number" min="0" value={comments} onChange={(event) => setComments(Number(event.target.value))} />
          </label>
          <label>
            Watch Time
            <input
              type="number"
              min="0"
              value={watchTime}
              onChange={(event) => setWatchTime(Number(event.target.value))}
            />
          </label>
          <label>
            CTR
            <input type="number" min="0" step="0.1" value={ctr} onChange={(event) => setCtr(Number(event.target.value))} />
          </label>
        </div>
      </section>

      <section className="analytics-panel">
        <h2>History</h2>
        {rows.length === 0 ? (
          <p className="muted">No analytics captured yet.</p>
        ) : (
          <div className="analytics-table">
            <div className="analytics-row analytics-row-head">
              <span>Topic</span>
              <span>Views</span>
              <span>CTR</span>
              <span>Score</span>
            </div>
            {rows.map((row) => (
              <div key={row.id} className="analytics-row">
                <span>{row.topic_title || row.video_id}</span>
                <span>{row.views.toLocaleString()}</span>
                <span>{row.click_through_rate}%</span>
                <strong>{row.topic_score}</strong>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
