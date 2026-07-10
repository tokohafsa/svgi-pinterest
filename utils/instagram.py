import yt_dlp
import os
import re


def _extract_username_from_url(url: str) -> str:
    """Extract IG username from profile URL like https://www.instagram.com/motiongraphics999/"""
    match = re.search(r"instagram\.com/([A-Za-z0-9_.]+)/?", url or "")
    if match:
        username = match.group(1)
        # Exclude known non-username paths
        if username not in ("p", "reel", "reels", "tv", "stories", "explore", "accounts"):
            return username
    return ""


def fetch_ig_metadata(url: str) -> dict:
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            description = info.get("description", "")

            # Priority 1: extract from uploader_url (most reliable)
            uploader_id = _extract_username_from_url(info.get("uploader_url", ""))

            # Priority 2: uploader_id field if it looks like a username (not numeric, no spaces)
            if not uploader_id:
                raw = info.get("uploader_id", "")
                if raw and not str(raw).isdigit() and " " not in str(raw):
                    uploader_id = str(raw).lstrip("@")

            # Priority 3: channel field
            if not uploader_id:
                raw = info.get("channel", "")
                if raw and not str(raw).isdigit() and " " not in str(raw):
                    uploader_id = str(raw).lstrip("@")

            # Priority 4: extract from channel_url
            if not uploader_id:
                uploader_id = _extract_username_from_url(info.get("channel_url", ""))

            # Priority 5: first @mention in caption
            if not uploader_id:
                mentions = re.findall(r"@([\w.]+)", description)
                if mentions:
                    uploader_id = mentions[0]

            return {
                "title": info.get("title", ""),
                "description": description,
                "uploader": info.get("uploader", ""),
                "uploader_id": uploader_id,
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "url": url,
            }
    except Exception as e:
        raise RuntimeError(f"Failed to fetch IG metadata: {str(e)}")


def download_ig_video(url: str, output_dir: str) -> str:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": os.path.join(output_dir, "video_%(id)s.%(ext)s"),
        "format": "mp4/best[ext=mp4]/best",
        "merge_output_format": "mp4",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not filename.endswith(".mp4"):
                filename = os.path.splitext(filename)[0] + ".mp4"
            if not os.path.exists(filename):
                for f in os.listdir(output_dir):
                    if f.endswith(".mp4"):
                        filename = os.path.join(output_dir, f)
                        break
            return filename
    except Exception as e:
        raise RuntimeError(f"Failed to download video: {str(e)}")
