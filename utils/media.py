import subprocess
import os
import tempfile
import requests
import imageio_ffmpeg


def download_direct(url: str, output_dir: str) -> str:
    """
    Download media from direct URL (mp4 or gif).
    Returns local file path.
    """
    ext = url.split("?")[0].split(".")[-1].lower()
    if ext not in ("mp4", "gif", "mov", "webm"):
        ext = "mp4"

    out_path = os.path.join(output_dir, f"media.{ext}")
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    with open(out_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return out_path


def convert_to_mp4(input_path: str, output_dir: str) -> str:
    """
    Convert GIF (or any format) to MP4 via ffmpeg.
    Returns path to mp4 file.
    """
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out_path = os.path.join(output_dir, "media_converted.mp4")

    subprocess.run([
        ffmpeg, "-y",
        "-i", input_path,
        "-movflags", "faststart",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # ensure even dimensions
        out_path
    ], capture_output=True, check=True)

    return out_path


def get_duration(video_path: str) -> int:
    """Get video duration in seconds via ffmpeg."""
    import re
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run([ffmpeg, "-i", video_path], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", result.stderr)
    if match:
        h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
        return int(h * 3600 + m * 60 + s)
    return 15
