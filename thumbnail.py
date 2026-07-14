import subprocess
import os
import base64
import tempfile
import hashlib
import imageio_ffmpeg


def extract_frames(video_path: str, seconds: list) -> dict:
    """
    Extract frames from video at specified seconds.
    Returns dict: {second: base64_jpeg_string}
    Uses video_path hash as unique prefix to avoid cross-video contamination.
    """
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    frames = {}

    # Unique prefix per video to avoid stale frames from previous video
    video_hash = hashlib.md5(video_path.encode()).hexdigest()[:8]
    tmp_dir = tempfile.gettempdir()

    # Clean up any old frames from previous videos
    for f in os.listdir(tmp_dir):
        if f.startswith("svgi_thumb_") and not f.startswith(f"svgi_thumb_{video_hash}_"):
            try:
                os.remove(os.path.join(tmp_dir, f))
            except Exception:
                pass

    for sec in seconds:
        out = os.path.join(tmp_dir, f"svgi_thumb_{video_hash}_{sec:03d}.jpg")
        result = subprocess.run([
            ffmpeg, "-y",
            "-ss", str(sec),
            "-i", video_path,
            "-frames:v", "1",
            "-q:v", "5",
            "-vf", "scale=240:-1",
            out
        ], capture_output=True)

        if os.path.exists(out) and os.path.getsize(out) > 0:
            with open(out, "rb") as f:
                frames[sec] = base64.b64encode(f.read()).decode("utf-8")

    return frames


def format_timestamp(sec: int) -> str:
    m, s = divmod(sec, 60)
    return f"{m}:{s:02d}"
