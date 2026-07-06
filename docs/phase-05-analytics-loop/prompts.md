# Phase 5: Analytics Loop — Prompts & Templates

## YouTube Analytics Scope

```
https://www.googleapis.com/auth/youtube.readonly
```

Added alongside existing `youtube.upload` scope for analytics pulling.

## TTS Speech Rate Options

| Label | Rate Value | Use Case |
|---|---|---|
| Slow | `-30%` | Slow narration, dramatic pacing |
| Slower | `-15%` | Slightly slower, easier to follow |
| Normal | `+0%` | Default speed |
| Faster | `+15%` | Faster narration, energetic content |
| Fast | `+30%` | Maximum speed (still intelligible) |

## Background Music Parameters

| Parameter | Value | Description |
|---|---|---|
| Noise type | `pink` | Pink noise (softer than white) |
| Noise volume | `0.05` | Background ambient level |
| Sine frequency | `110 Hz` | Sub-audible drone (A2 note) |
| Sine volume | `0.03` | Very subtle |
| Mix volume | `0.1` | Final ambient level (10% of original) |
| Sample rate | `44100 Hz` | CD quality |
| Channels | `1 (mono)` | Mono for small file size |
| Bitrate | `48 kbps` | Adequate for ambient |

## Environment Variables (No Changes from Phase 4)

```env
YOUTUBE_CLIENT_ID=your_client_id.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_TOKEN_PATH=data/youtube_token.json
```

## API Query Parameters

### Render Video
```
POST /api/videos/render/{topic_id}?background_music=true
POST /api/videos/render/{topic_id}?background_music=false
```

### Generate TTS
```
POST /api/videos/tts/{topic_id}?rate=+0%
POST /api/videos/tts/{topic_id}?rate=+15%
POST /api/videos/tts/{topic_id}?rate=-30%
```

## Dashboard Insights Template

```
Total Views: {n}
Average Interest Score: {n.n}
Top Topic: {title}
Topics Analysed: {n}

Recent Performance Feed:
  {title} — {views} views — Score: {score}
  {title} — {views} views — Score: {score}
  ...
```

## Score Formula Reference

```
interest_score = (
    AVG(normalized_likes, normalized_comments, normalized_views) * 0.7
    + LOG10(views + 1) / 5 * 100 * 0.3
) * (1 - DECAY)

Where:
  normalised value = (value / max_in_set) * 100
  DECAY = 0.3 (30% penalty per update cycle)
```
