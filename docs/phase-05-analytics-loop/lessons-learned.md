# Phase 5: Analytics Loop — Lessons Learned

## Design Decisions

### 1. Analytics Pull via Background Task
- `POST /analytics/pull` runs synchronously — fine for a few videos but would benefit from background task + job tracking at scale
- The puller iterates all uploaded videos and fetches stats one-by-one (sequential, no batching)
- YouTube Data API `videos.list` supports up to 50 video IDs per request — a future optimization

### 2. Interest Score Formula
- Score = `avg_score * 0.7 + views_factor * 0.3`
- `avg_score` normalizes likes/comments/views per video
- `views_factor` uses `log10(views)` to prevent viral videos from drowning out smaller ones
- `_TOPIC_SCORE_DECAY = 0.7` applies a 30% penalty per update cycle to prevent score inflation

### 3. FFmpeg-Generated Background Music
- Ambient audio is generated at render time via lavfi filters (`anoisesrc` + `sine`)
- Mixed at low volume (0.1) behind existing TTS narration
- No audio files to store — generated on-the-fly
- Pink noise avoids the harshness of white noise; 110 Hz sine gives a subtle drone

### 4. TTS Speech Rate via Query Parameter
- edge-tts natively supports a `rate` parameter (e.g. `+15%`, `-30%`)
- Exposed as a query parameter on the API (`/tts/{topic_id}?rate=+15%`)
- Frontend provides a dropdown with 5 presets (Slow → Fast)

### 5. Async YouTube Upload with Job Polling
- Upload runs as a `BackgroundTasks` task that creates a pipeline job
- Frontend polls `GET /pipeline/jobs/{job_id}` every 2 seconds
- Job transitions: `PENDING → RUNNING → COMPLETE | FAILED`
- Upload progress shown as "Uploading (RUNNING)..." in the UI

## Gotchas

### YouTube API Quotas
- `videos.list(part="statistics")` costs 1 unit per video
- For 10 uploaded videos, a full pull costs 10 units
- Consider caching or scheduled pulls to stay within daily quota (10,000 units)

### Score Migration
- Adding `interest_score` to existing topics requires a schema migration
- `init_db()` must be called to apply `ALTER TABLE` statements
- Existing topics start with `NULL` scores until analytics are pulled

### Background Music Volume
- Too low → inaudible; too high → distracts from narration
- 0.1 ambient volume + 0.03 sine + 0.05 noise provides a good baseline
- Consider making this configurable in the future

### edge-tts Rate Limits
- Extreme rates (±50%+) can produce distorted or unintelligible audio
- Limited to ±30% in the UI, which edge-tts handles well

## Future Improvements

- Scheduled analytics pull (cron job)
- YouTube Data API quota usage dashboard
- Interest score trends over time (chart on Dashboard)
- AI-powered content gap analysis based on low-performer topics
- Configurable background music volume
- Multi-voice TTS per scene (e.g., narrator vs. interviewee)
- Upload progress with percentage (requires chunk-level tracking in the backend)
