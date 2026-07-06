"""Tests for Phase 3 video pipeline."""

from pathlib import Path
import uuid

import pytest

from backend.assets.manager import store_asset, get_assets_for_topic, get_assets_for_scene, delete_asset, bulk_store_assets
from backend.video.scenes import split_script_into_scenes, save_scenes, get_scenes_for_topic
from backend.video.renderer import _COLORS
from backend.research.image_extractor import _is_image_url


class TestScenes:
    def test_split_empty_script(self):
        scenes = split_script_into_scenes("")
        assert len(scenes) == 0

    def test_split_with_visual_markers(self):
        script = "[VISUAL] Scene one content.\n\n[VISUAL] Scene two content."
        scenes = split_script_into_scenes(script)
        assert len(scenes) == 2
        assert scenes[0]["text"] == "Scene one content."
        assert scenes[1]["text"] == "Scene two content."

    def test_split_respects_max_scenes(self):
        text = "\n\n".join([f"This is paragraph number {i} in the script." for i in range(20)])
        scenes = split_script_into_scenes(text, max_scenes=5)
        assert len(scenes) == 5

    def test_scene_duration_bounds(self):
        scenes = split_script_into_scenes("Short.")
        d = scenes[0]["duration"]
        assert 30.0 <= d <= 50.0

    def test_split_plain_text(self):
        text = "First paragraph about history. It explains many things.\n\nSecond paragraph about impact."
        scenes = split_script_into_scenes(text)
        assert len(scenes) == 2

    def test_save_and_get_scenes(self, sample_topic, db_conn):
        import uuid as _uuid
        script_id = str(_uuid.uuid4())
        db_conn.execute(
            "INSERT INTO scripts (id, topic_id, content, status) VALUES (?, ?, ?, ?)",
            (script_id, sample_topic, "Scene A.\n\nScene B.", "APPROVED"),
        )
        db_conn.commit()

        saved = save_scenes(script_id, sample_topic, "Scene A.\n\nScene B.")
        assert len(saved) >= 1
        assert saved[0]["script_id"] == script_id

        scenes = get_scenes_for_topic(sample_topic)
        assert len(scenes) >= 1


class TestAssetManager:
    def test_store_and_get_asset(self, sample_topic):
        asset = store_asset("image", "/fake/path/img.jpg", sample_topic)
        assert asset["type"] == "image"
        assert asset["topic_id"] == sample_topic
        assert asset["id"] is not None

    def test_get_assets_by_type(self, sample_topic):
        store_asset("image", "/img.jpg", sample_topic)
        store_asset("audio", "/audio.mp3", sample_topic)

        images = get_assets_for_topic(sample_topic, "image")
        assert len(images) == 1
        assert images[0]["type"] == "image"

        all_assets = get_assets_for_topic(sample_topic)
        assert len(all_assets) == 2

    def test_asset_with_scene_id(self, sample_topic):
        scene_id = str(uuid.uuid4())
        store_asset("audio", "/audio.mp3", sample_topic, scene_id=scene_id)
        scene_assets = get_assets_for_scene(scene_id)
        assert len(scene_assets) == 1
        assert scene_assets[0]["scene_id"] == scene_id

    def test_delete_asset(self, sample_topic, tmp_path):
        test_file = tmp_path / "test.jpg"
        test_file.write_text("fake-image-data")

        asset = store_asset("image", str(test_file), sample_topic)
        result = delete_asset(asset["id"])
        assert result is True
        assert not test_file.exists()

    def test_delete_nonexistent_asset(self):
        result = delete_asset("nonexistent-id")
        assert result is False

    def test_bulk_store(self, sample_topic):
        assets = [
            {"type": "image", "file_path": "/img1.jpg", "topic_id": sample_topic},
            {"type": "image", "file_path": "/img2.jpg", "topic_id": sample_topic},
        ]
        stored = bulk_store_assets(assets)
        assert len(stored) == 2
        assert stored[0]["type"] == "image"


class TestImageExtractor:
    def test_is_image_url_valid_extensions(self):
        assert _is_image_url("https://example.com/photo.jpg")
        assert _is_image_url("https://example.com/photo.png")
        assert _is_image_url("https://example.com/photo.webp")

    def test_is_image_url_invalid(self):
        assert not _is_image_url("https://example.com/page.html")
        assert not _is_image_url("https://example.com/script.js")

    def test_is_image_url_no_extension(self):
        assert not _is_image_url("https://example.com/photo")


class TestRenderer:
    def test_colors_defined(self):
        assert len(_COLORS) == 10
        for c in _COLORS:
            assert c.startswith("0x")
            assert len(c) == 8  # 0x + 6 hex chars
