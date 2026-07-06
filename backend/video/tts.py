from __future__ import annotations

import asyncio
import logging
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

import edge_tts

from backend.core.config import settings

PROJECTS_DIR = Path(__file__).parent.parent.parent / "data" / "projects"


async def generate_scene_audio(
    text: str,
    topic_id: str,
    scene_id: str,
    voice: str | None = None,
    rate: str | None = None,
) -> str:
    audio_dir = PROJECTS_DIR / topic_id / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / f"scene-{scene_id[:8]}.mp3"

    communicate = edge_tts.Communicate(
        text,
        voice or settings.tts_voice,
        rate=rate or "+0%",
    )
    await asyncio.wait_for(
        communicate.save(str(output_path)),
        timeout=settings.tts_timeout_seconds,
    )

    return str(output_path)


async def generate_all_scene_audio(
    scenes: list[dict],
    topic_id: str,
    rate: str | None = None,
    voice: str | None = None,
    max_concurrent: int = 3,
) -> list[dict]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def throttled_generate(scene: dict) -> tuple[str, str | Exception]:
        async with semaphore:
            for attempt in range(3):
                try:
                    path = await generate_scene_audio(
                        scene["text"], topic_id, scene["id"], voice=voice, rate=rate,
                    )
                    return scene["id"], path
                except Exception as e:
                    if attempt < 2:
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                    return scene["id"], e

    results = await asyncio.gather(
        *[throttled_generate(s) for s in scenes], return_exceptions=True,
    )

    audio_map: dict[str, str] = {}
    for r in results:
        if isinstance(r, Exception):
            continue
        scene_id, path_or_err = r
        if isinstance(path_or_err, Exception):
            logger.warning("TTS failed for scene %s: %s", scene_id, path_or_err)
            continue
        if not Path(path_or_err).exists():
            continue
        audio_map[scene_id] = path_or_err

    return [
        {"scene_id": sid, "audio_path": path}
        for sid, path in audio_map.items()
    ]
