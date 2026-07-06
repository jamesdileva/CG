# Phase 3: Video Pipeline — Code Examples

## 1. Generate TTS Audio for All Scenes

```python
import asyncio
from backend.video.tts import generate_all_scene_audio

scenes = [
    {"id": "scene-1", "text": "In 1919, Boston experienced..."},
    {"id": "scene-2", "text": "The molasses tank stood 50 feet tall..."},
]
topic_id = "your-topic-uuid"

results = asyncio.run(generate_all_scene_audio(scenes, topic_id))
for r in results:
    print(f"Scene {r['scene_id']}: audio saved to {r['audio_path']}")
```

## 2. Extract Images from Research Sources

```python
from backend.research.image_extractor import extract_images_for_topic

images = asyncio.run(extract_images_for_topic("topic-uuid"))
for img in images:
    print(f"Downloaded {img['file_path']} from {img['source_url']}")
```

## 3. Store Assets in Database

```python
from backend.assets.manager import store_asset, get_assets_for_topic

# Store a single asset
asset = store_asset(
    asset_type="image",
    file_path="data/projects/.../images/img-01.jpg",
    topic_id="topic-uuid",
    source_url="https://example.com/image.jpg",
)

# Bulk store
from backend.assets.manager import bulk_store_assets
assets = [
    {"type": "audio", "file_path": "...", "topic_id": "...", "scene_id": "..."},
    {"type": "image", "file_path": "...", "topic_id": "...", "source_url": "..."},
]
stored = bulk_store_assets(assets)

# Query assets
all_assets = get_assets_for_topic("topic-uuid")
audio_only = get_assets_for_topic("topic-uuid", asset_type="audio")
```

## 4. Render a Scene-Based Video

```python
from backend.video.renderer import render_scene_based_video, render_scene_video

# Render a single scene as a standalone clip
clip = render_scene_video(
    scene={"text": "Hello world", "duration": 6.0},
    scene_index=0,
    topic_id="topic-uuid",
    audio_path="data/projects/.../audio/scene-....mp3",
)

# Render full video from scenes
result = render_scene_based_video(
    topic_id="topic-uuid",
    title="My Documentary",
    scenes=[{...}, {...}],
    scene_audio_map={"scene-id": "path/to/audio.mp3"},
    scene_image_map={"scene-id": "path/to/image.jpg"},
)
print(f"Output: {result['file_path']}")
print(f"Duration: {result['duration_seconds']}s")
print(f"Size: {result['file_size_bytes']} bytes")
```

## 5. Generate Thumbnail

```python
from backend.video.renderer import generate_thumbnail

thumb_path = generate_thumbnail("data/projects/.../video/documentary-mvp.mp4")
print(f"Thumbnail: {thumb_path}")
```

## 6. Full API Workflow (curl)

```bash
# 1. Generate TTS audio for scene narration
curl -X POST http://localhost:8000/api/videos/tts/{topic_id}

# 2. Check TTS status
curl http://localhost:8000/api/videos/tts/{topic_id}

# 3. Extract images from research sources
curl -X POST http://localhost:8000/api/videos/images/{topic_id}

# 4. List all assets
curl http://localhost:8000/api/videos/assets/{topic_id}

# 5. Render video (uses audio + images if available)
curl -X POST http://localhost:8000/api/videos/render/{topic_id}

# 6. Generate thumbnail from rendered video
curl -X POST http://localhost:8000/api/videos/thumbnail/{topic_id}
```
