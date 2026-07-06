# Phase 3: Video Pipeline — Prompts & Templates

## TTS Voice Configuration

The default voice is `en-US-JennyNeural` (Microsoft Neural voice).

Available voices can be listed with:
```bash
edge-tts --list-voices
```

Set via `.env`:
```env
TTS_VOICE=en-US-JennyNeural
```

## Scene Image Extraction

Image extraction does not use LLM prompts. It works by:
1. Re-fetching research source HTML pages
2. Parsing `<img>` tags
3. Downloading valid image files (jpg, png, webp, gif)

## FFmpeg Scene Composition

Each scene is built with the following filter chain:

```
color=c={hex_color}:s=1280x720:d={duration}
  → [optional] scale/crop image overlay
  → drawtext=caption (28px, white, centered, with semi-transparent box)
  → format=yuv420p
```

Audio is added with:
```
-c:a aac -shortest
```

## Color Palette (per scene index)

| Index | Color | Hex |
|---|---|---|
| 0 | Slate 800 | `#1e293b` |
| 1 | Slate 700 | `#334155` |
| 2 | Teal 700 | `#0f766e` |
| 3 | Blue 700 | `#1d4ed8` |
| 4 | Violet 600 | `#7c3aed` |
| 5 | Rose 700 | `#be123c` |
| 6 | Amber 700 | `#b45309` |
| 7 | Green 800 | `#15803d` |
| 8 | Cyan 700 | `#0e7490` |
| 9 | Purple 700 | `#6b21a8` |
