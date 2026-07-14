##FIX ke2
import subprocess
import os
import base64
import tempfile
import imageio_ffmpeg


def extract_frames(video_path: str, seconds: list[int]) -> dict[int, str]:
    """
    Extract frames from video at specified seconds.
    Returns dict: {second: base64_jpeg_string}
    """
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    frames = {}

    for sec in seconds:
        out = os.path.join(tempfile.gettempdir(), f"thumb_{sec:02d}.jpg")
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
