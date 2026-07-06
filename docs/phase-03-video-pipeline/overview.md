# Phase 3: Video Pipeline — Overview

## Goal

Transform approved scripts into rendered MP4 videos with TTS narration, scene images extracted from research, and thumbnail generation.

## What Was Built

### Backend

| Module | File | Purpose |
|---|---|---|
| TTS Engine | `backend/video/tts.py` | edge-tts per-scene audio narration |
| Image Extraction | `backend/research/image_extractor.py` | Extract images from research source HTML |
| Asset Manager | `backend/assets/manager.py` | CRUD for images, audio, thumbnails in DB |
| FFmpeg Renderer | `backend/video/renderer.py` | Scene composition, audio overlay, concatenation |
| Thumbnail Gen | `backend/video/renderer.py` | Frame extraction from rendered video |

### Frontend

| Page | Updates |
|---|---|
| Production (`Production.tsx`) | TTS generation, image extraction, thumbnail, asset gallery |

### Database

| Table | Purpose |
|---|---|
| `assets` | Tracks images, audio files, and thumbnails per topic/scene |

---

## Pipeline Flow

```
Script Approved
       ↓
Scene Splitting (existing)
       ↓
TTS Generation  ───→ Audio files stored as assets
       ↓
Image Extraction ───→ Images from research stored as assets
       ↓
Scene Render (per scene)
  ├── Colored background (or image overlay)
  ├── TTS audio narration
  └── Caption text overlay
       ↓
Scene Concatenation → Final MP4
       ↓
Thumbnail Extraction → JPEG thumbnail asset
       ↓
Video Rendered (state transition)
```

## Key Decisions

- **TTS**: edge-tts (free, high-quality Microsoft Edge voices, async Python library)
- **Scene visuals**: Colored backgrounds with caption text, images from research sources (no AI generation)
- **Asset tracking**: Dedicated `assets` SQLite table for queryable media management
