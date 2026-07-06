from __future__ import annotations

import json
import logging
import math
import os
from pathlib import Path
import shutil
import subprocess
import textwrap

logger = logging.getLogger(__name__)

from backend.video.scenes import PROJECTS_DIR


_IMAGE_MAGIC: list[tuple[bytes, int]] = [
    (b"\xff\xd8\xff", 0),       # JPEG
    (b"\x89PNG", 0),            # PNG
    (b"GIF8", 0),               # GIF
    (b"RIFF", 0),               # WebP (RIFF....WEBP)
]

_AUDIO_MIN_BYTES = 1024  # smallest valid MP3 with actual audio frames
_AUDIO_FFPROBE_BYTES = 50000  # skip ffprobe for files this large (always valid)


def _is_valid_image_file(path: str | Path) -> bool:
    p = Path(path)
    if not p.exists() or p.stat().st_size < 512:
        return False
    try:
        with p.open("rb") as f:
            head = f.read(16)
        for magic, offset in _IMAGE_MAGIC:
            if head[offset:offset + len(magic)] == magic:
                if magic == b"RIFF" and head[8:12] != b"WEBP":
                    continue
                return True
    except Exception:
        pass
    return False


def _is_valid_audio_file(path: str | Path) -> bool:
    """Check if an audio file is valid. Skips slow ffprobe for large files."""
    p = Path(path)
    if not p.exists() or p.stat().st_size < _AUDIO_MIN_BYTES:
        return False
    # Files above 50KB are almost certainly valid MP3s — skip ffprobe
    if p.stat().st_size >= _AUDIO_FFPROBE_BYTES:
        return True
    ffprobe = shutil.which("ffprobe") or str(Path(_get_ffmpeg()).parent / "ffprobe.exe")
    try:
        result = subprocess.run(
            [ffprobe, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return False
        duration = float(result.stdout.strip())
        return duration > 0.1
    except Exception:
        return False


def _find_windows_font() -> str | None:
    """Copy a Windows font to a data/fonts/ subdirectory and return relative path (no colons)."""
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/Calibri.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    for src in candidates:
        src_path = Path(src)
        if src_path.exists():
            dst = PROJECTS_DIR.parent.parent / "data" / "fonts" / src_path.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                import shutil
                shutil.copy2(str(src_path), str(dst))
            # Return path relative to CWD so there's no drive letter colon
            try:
                rel = dst.relative_to(Path.cwd())
                return rel.as_posix()
            except ValueError:
                return dst.as_posix()
    return None


_DRAWTEXT_FONT = _find_windows_font()


_COLORS = [
    "0x1e293b", "0x334155", "0x0f766e", "0x1d4ed8",
    "0x7c3aed", "0xbe123c", "0xb45309", "0x15803d",
    "0x0e7490", "0x6b21a8",
]

_FFMPEG_COLOR = "0x111827"


def _write_textfile(scene_id: str, text: str, topic_id: str) -> Path:
    """Write caption text to a file for ffmpeg's textfile option (avoids escaping issues)."""
    text_dir = PROJECTS_DIR / topic_id / "video" / "textfiles"
    text_dir.mkdir(parents=True, exist_ok=True)
    path = text_dir / f"{scene_id}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def _get_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not available on PATH")
    return ffmpeg


def render_placeholder_video(topic_id: str, title: str, scenes: list[dict]) -> dict:
    ffmpeg = _get_ffmpeg()
    project_dir = PROJECTS_DIR / topic_id
    video_dir = project_dir / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    output_path = video_dir / "documentary-mvp.mp4"

    duration = max(8, int(sum(float(scene.get("duration", 8.0)) for scene in scenes)))
    scene_count = len(scenes)
    text = f"{title}\n\nMVP render\n{scene_count} scenes"
    wrapped = "\n".join(textwrap.wrap(text, width=34, replace_whitespace=False))
    textfile = _write_textfile("placeholder", wrapped, topic_id)
    textfile_rel = os.path.relpath(textfile, Path.cwd()).replace("\\", "/")
    font_opt = f":fontfile={_DRAWTEXT_FONT}" if _DRAWTEXT_FONT else ""
    drawtext = (
        "drawtext="
        f"textfile={textfile_rel}:"
        f"fontcolor=white:fontsize=42{font_opt}:line_spacing=16:"
        "x=(w-text_w)/2:y=(h-text_h)/2"
    )

    command = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", f"color=c={_FFMPEG_COLOR}:s=1280x720:d={duration}",
        "-vf", drawtext,
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)

    return {
        "file_path": str(output_path),
        "duration_seconds": duration,
        "file_size_bytes": output_path.stat().st_size,
    }


def render_scene_video(
    scene: dict,
    scene_index: int,
    topic_id: str,
    audio_path: str | None = None,
    image_path: str | None = None,
    image_caption: str = "",
    output_dir: Path | None = None,
) -> Path:
    ffmpeg = _get_ffmpeg()
    output_dir = output_dir or (PROJECTS_DIR / topic_id / "video" / "scenes")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"scene-{scene_index:03d}.mp4"

    duration = float(scene.get("duration", 8.0))
    color = _COLORS[scene_index % len(_COLORS)]

    caption = "\n".join(textwrap.wrap(scene["text"], width=42, replace_whitespace=False))
    caption = caption[:600]
    textfile = _write_textfile(scene["id"], caption, topic_id)

    has_valid_audio = audio_path and _is_valid_audio_file(audio_path)

    # Validate image file (reject corrupt/invalid images)
    if image_path and Path(image_path).exists() and _is_valid_image_file(image_path):
        inputs = ["-loop", "1", "-i", image_path]
        filter_parts = [
            "format=rgb24,scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
        ]
    else:
        vid_duration = 600 if has_valid_audio else duration
        inputs = ["-f", "lavfi", "-i", f"color=c={color}:s=1280x720:d={vid_duration}"]
        filter_parts = []

    # Use a relative path with forward slashes to avoid ffmpeg drawtext escape issues
    textfile_rel = os.path.relpath(textfile, Path.cwd()).replace("\\", "/")
    font_opt = f":fontfile={_DRAWTEXT_FONT}" if _DRAWTEXT_FONT else ""
    filter_parts.append(
        f"drawtext=textfile={textfile_rel}:fontcolor=white:fontsize=28"
        f"{font_opt}:"
        f"line_spacing=12:x=(w-text_w)/2:y=(h-text_h)/2+40:"
        f"box=1:boxcolor=black@0.5"
    )

    # Image caption overlay (bottom of screen)
    if image_caption:
        capfile = _write_textfile(f"cap-{scene['id']}", image_caption, topic_id)
        capfile_rel = os.path.relpath(capfile, Path.cwd()).replace("\\", "/")
        filter_parts.append(
            f"drawtext=textfile={capfile_rel}:fontcolor=white:fontsize=16"
            f"{font_opt}:"
            f"x=(w-text_w)/2:y=h-text_h-20:"
            f"box=1:boxcolor=black@0.5"
        )

    filter_parts.append(f"format=yuv420p")
    filter_str = ",".join(filter_parts)

    cmd = [ffmpeg, "-y"] + inputs

    if has_valid_audio:
        cmd += ["-i", audio_path]
        cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest"]
        logger.info("Scene %d: including audio %s", scene_index, audio_path)
    else:
        if audio_path and Path(audio_path).exists():
            logger.warning("Scene %d: corrupt audio %s, rendering without audio", scene_index, audio_path)
        cmd += ["-c:v", "libx264", "-preset", "ultrafast"]

    cmd += ["-vf", filter_str]
    cmd += ["-pix_fmt", "yuv420p"]

    # Without audio, set explicit duration so the video doesn't loop forever
    if not has_valid_audio:
        cmd += ["-t", str(duration)]

    cmd += [str(output_path)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("ffmpeg failed for scene %d (exit %d)", scene_index, result.returncode)
        logger.error("ffmpeg stderr:\n%s", result.stderr[:3000])
        raise RuntimeError(f"ffmpeg scene {scene_index} failed (exit {result.returncode})")
    return output_path


def render_scene_based_video(
    topic_id: str,
    title: str,
    scenes: list[dict],
    scene_audio_map: dict[str, str] | None = None,
    scene_image_map: dict[str, str] | None = None,
    scene_caption_map: dict[str, str] | None = None,
    background_music: bool = True,
) -> dict:
    ffmpeg = _get_ffmpeg()
    project_dir = PROJECTS_DIR / topic_id
    video_dir = project_dir / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    concat_output = video_dir / "documentary-concat.mp4"
    output_path = video_dir / "documentary-mvp.mp4"

    scene_audio_map = scene_audio_map or {}
    scene_image_map = scene_image_map or {}
    scene_caption_map = scene_caption_map or {}

    scene_videos: list[Path] = []
    total_duration = 0.0

    for idx, scene in enumerate(scenes):
        audio = scene_audio_map.get(scene["id"])
        # Defensive: skip audio if the file doesn't exist
        if audio and not Path(audio).exists():
            audio = None
        image = scene_image_map.get(scene["id"])
        if image and not Path(image).exists():
            image = None
        caption = scene_caption_map.get(scene["id"], "")
        clip_path = render_scene_video(scene, idx, topic_id, audio, image, caption, video_dir / "scenes")
        scene_videos.append(clip_path)
        total_duration += float(scene.get("duration", 8.0))

    concat_path = video_dir / "concat.txt"
    concat_path.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in scene_videos),
        encoding="utf-8",
    )

    audio_count = sum(1 for s in scenes if scene_audio_map.get(s["id"]) and Path(scene_audio_map[s["id"]]).exists())
    logger.info("Rendering %d scenes for topic %s (%d with audio)", len(scenes), topic_id, audio_count)

    cmd = [
        ffmpeg, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_path),
        "-c", "copy",
        str(concat_output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning("Concat stderr: %s", result.stderr[:500])
        raise RuntimeError(f"Concat failed: {result.stderr[:500]}")
    logger.info("Concat succeeded: %s", concat_output)

    if background_music:
        ambient = generate_ambient_audio(total_duration, video_dir)
        _mix_audio(concat_output, ambient, output_path)
        concat_output.unlink(missing_ok=True)
    else:
        output_path = concat_output

    return {
        "file_path": str(output_path),
        "duration_seconds": int(total_duration),
        "file_size_bytes": output_path.stat().st_size,
    }


def generate_thumbnail(video_path: str | Path, output_dir: Path | None = None) -> str:
    ffmpeg = _get_ffmpeg()
    video_path = Path(video_path)
    output_dir = output_dir or video_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_path = output_dir / "thumbnail.jpg"

    duration_cmd = [
        ffmpeg, "-i", str(video_path),
        "-f", "null", "-",
    ]
    result = subprocess.run(
        duration_cmd, capture_output=True, text=True, check=False,
    )
    duration_match = __import__("re").search(
        r"Duration: (\d+):(\d+):(\d+)\.(\d+)", result.stderr,
    )
    if duration_match:
        h, m, s, ms = map(int, duration_match.groups())
        total_sec = h * 3600 + m * 60 + s + ms / 100
    else:
        total_sec = 10

    seek = max(1, int(total_sec * 0.3))

    cmd = [
        ffmpeg, "-y",
        "-ss", str(seek),
        "-i", str(video_path),
        "-vframes", "1",
        "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
        str(thumbnail_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    return str(thumbnail_path)


def generate_ambient_audio(duration: float, output_dir: Path) -> str:
    ffmpeg = _get_ffmpeg()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "ambient.mp3"

    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", f"anoisesrc=d={duration}:c=pink:a=0.05",
        "-f", "lavfi",
        "-i", f"sine=frequency=110:duration={duration}",
        "-filter_complex",
        "[1:a]volume=0.03[hum];[0:a][hum]amix=inputs=2:duration=first[out]",
        "-map", "[out]",
        "-ar", "44100",
        "-ac", "1",
        "-b:a", "48k",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Ambient audio generation failed: {result.stderr}")
    return str(output_path)


def _mix_audio(
    video_path: Path,
    ambient_path: str,
    output_path: Path,
    ambient_volume: float = 0.1,
) -> Path:
    ffmpeg = _get_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-i", ambient_path,
        "-filter_complex",
        f"[1:a]volume={ambient_volume}[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_path),
    ]
    logger.info("Mixing audio: %s", " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Audio mix failed: %s", result.stderr)
        raise RuntimeError(f"Audio mix failed: {result.stderr}")
    return output_path
