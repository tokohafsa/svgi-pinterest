import yt_dlp
import os
import re
from urllib.parse import urlparse, parse_qs


def _parse_img_index(url: str):
    """
    Parse ?img_index=N dari URL Instagram carousel.
    Instagram pakai 1-based index, yt-dlp playlist_items juga 1-based.
    Return string '2' untuk img_index=2, atau None kalau bukan carousel.
    """
    qs = parse_qs(urlparse(url).query)
    val = qs.get("img_index", [None])[0]
    if val and val.isdigit():
        return val
    return None


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
    img_index = _parse_img_index(url)

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if img_index:
        ydl_opts["playlist_items"] = img_index

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Kalau carousel, yt-dlp return dict dengan key 'entries'
            # Ambil entry yang sesuai index, bukan seluruh playlist
            if info.get("_type") == "playlist" and info.get("entries"):
                entries = [e for e in info["entries"] if e is not None]
                info = entries[0] if entries else info

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
    img_index = _parse_img_index(url)

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": os.path.join(output_dir, "video_%(id)s.%(ext)s"),
        "format": "mp4/best[ext=mp4]/best",
        "merge_output_format": "mp4",
    }
    if img_index:
        ydl_opts["playlist_items"] = img_index

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Kalau carousel, info adalah playlist — ambil entry yang didownload
            if info.get("_type") == "playlist" and info.get("entries"):
                entries = [e for e in info["entries"] if e is not None]
                info = entries[0] if entries else info

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
