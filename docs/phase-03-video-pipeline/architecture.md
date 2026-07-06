# Phase 3: Video Pipeline — Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────┐
│              Production Studio UI                    │
│        (Scene list, TTS, Images, Render)             │
└────────────────────┬────────────────────────────────┘
                     │ HTTP REST
                     ▼
┌──────────────────────────────────────────────────────┐
│               FastAPI /api/videos/*                   │
│                                                       │
│  POST /tts/{id}    POST /images/{id}                 │
│  POST /render/{id} POST /thumbnail/{id}              │
│  GET /assets/{id}  GET /{id}                          │
└───────┬─────────────────────────┬────────────────────┘
        │                         │
        ▼                         ▼
┌───────────────┐       ┌──────────────────┐
│   TTS Engine  │       │  Image Extractor  │
│  (edge-tts)   │       │  (from research)  │
└───────┬───────┘       └────────┬─────────┘
        │                        │
        ▼                        ▼
┌──────────────────────────────────────────────────────┐
│                   FFmpeg Renderer                     │
│                                                       │
│  Scene 1: [background] + [audio] + [caption]          │
│  Scene 2: [background] + [audio] + [caption]          │
│  ...                                                  │
│  Concat → documentary-mvp.mp4                          │
└──────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────┐
│               Asset Manager                           │
│  Stores/retrieves every file in DB (assets table)     │
└──────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────┐
│                  File System                          │
│                                                       │
│  data/projects/{topic_id}/                            │
│   ├── scenes.json                                     │
│   ├── audio/ (per-scene MP3 files)                    │
│   ├── images/ (extracted from research)               │
│   └── video/ (scene clips + final MP4 + thumbnail)    │
└──────────────────────────────────────────────────────┘
```

## Data Flow

### TTS Generation
```
POST /api/videos/tts/{topic_id}
  → Load scenes from DB
  → generate_all_scene_audio() via edge-tts
  → Save MP3 to data/projects/{topic_id}/audio/
  → Store asset records in DB
  → Update scenes.audio_path in DB
```

### Image Extraction
```
POST /api/videos/images/{topic_id}
  → Load research source URLs from DB
  → Fetch HTML, extract <img> tags
  → Download valid images to data/projects/{topic_id}/images/
  → Store asset records in DB
```

### Video Render
```
POST /api/videos/render/{topic_id}
  → Split script into scenes (save_scenes)
  → Check for TTS audio assets per scene
  → If audio available:
      → render_scene_based_video()
        → For each scene:
            → FFmpeg: colored background + caption + audio
            → Output scene-{n}.mp4
        → Concat all scenes with FFmpeg concat demuxer
  → Else:
      → render_placeholder_video() (single text overlay)
  → Store video record in DB
  → Transition topic to VIDEO_RENDERED
```

### Thumbnail Extraction
```
POST /api/videos/thumbnail/{topic_id}
  → Load rendered video path
  → FFmpeg: seek to 30% → extract single frame
  → Save as thumbnail.jpg in video/ directory
  → Store asset record (type=thumbnail)
```
