# Phase 3: Video Pipeline — Lessons Learned

## Design Decisions

### 1. TTS Provider Choice: edge-tts
- **Why**: Free, async, excellent voice quality via Microsoft Edge neural voices
- **Trade-off**: Requires internet on first run (voice model download ~50MB), then cached locally
- **Alternatives considered**: pyttsx3 (offline but robotic), ElevenLabs API (paid, best quality)

### 2. No AI Image Generation
- Real images extracted from research sources feel more authentic for documentary content
- Users reported AI-generated images feel "slop-like" and reduce credibility
- Source attribution is preserved via `source_url` in the assets table

### 3. Assets Table vs Filesystem-Only
- Added a proper `assets` DB table for queryability
- Makes it easy to: list all images for a topic, find orphaned files, track asset provenance
- Scene `audio_path`/`image_path` columns provide fast lookup for the renderer

### 4. Two Render Modes
- **Scene-based renderer**: Used when TTS audio is available — produces proper per-scene clips with narration
- **Placeholder renderer**: Falls back when no audio exists — single text overlay for testing
- Keeps the pipeline functional even without TTS, enabling iterative development

## Gotchas

### FFmpeg Concat Demuxer
- Using `-f concat -safe 0` requires a text file with absolute paths
- All scene clips must have the same video codec for stream copy (`-c copy`)
- If adding audio mid-stream, switch to re-encode (`-c:v libx264 -c:a aac`)

### edge-tts Limitations
- Text is truncated at ~1000 characters per call for reliability
- Very long scenes should be split or the text trimmed
- Voice download happens on first `Communicate.save()` call, not on import

### Image Extraction
- Source HTML parsing is regex-based (`<img src="...">`) — fragile for some sites
- Wikipedia uses SVG placeholders that get filtered by extension whitelist
- Some CDN URLs timeout or block automated requests — User-Agent header helps

## Future Improvements

- Speech rate control per scene (edge-tts supports `rate` parameter)
- Background music track overlay behind narration
- Image-to-scene assignment UI (drag images onto scene cards)
- Multiple TTS providers selectable per scene
- Parallel render jobs for faster multi-topic production
