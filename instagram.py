import yt_dlp
import os
import re
from urllib.parse import urlparse, parse_qs


def _parse_img_index(url: str):
    """
    Parse ?img_index=N dari URL Instagram carousel.
    Return int (1-based), atau None kalau bukan carousel.
    """
    qs = parse_qs(urlparse(url).query)
    val = qs.get("img_index", [None])[0]
    if val and val.isdigit():
        return int(val)
    return None


def _strip_img_index(url: str) -> str:
    """Buang ?img_index= dari URL supaya yt-dlp fetch seluruh carousel."""
    return url.split("?")[0]


def _extract_username_from_url(url: str) -> str:
    """Extract IG username from profile URL like https://www.instagram.com/motiongraphics999/"""
    match = re.search(r"instagram\.com/([A-Za-z0-9_.]+)/?", url or "")
    if match:
        username = match.group(1)
        if username not in ("p", "reel", "reels", "tv", "stories", "explore", "accounts"):
            return username
    return ""


def _pick_entry(info: dict, img_index: int | None):
    """
    Dari hasil extract_info (mungkin playlist), pilih entry yang tepat.
    - Kalau bukan playlist: return info langsung.
    - Kalau playlist tanpa img_index: return entries[0].
    - Kalau playlist dengan img_index: ambil entry video ke-N
      (hitung hanya entries yang punya formats/video, bukan foto).
    """
    if info.get("_type") != "playlist":
        return info

    entries = [e for e in (info.get("entries") or []) if e is not None]
    if not entries:
        return info

    if img_index is None:
        return entries[0]

    # Filter: entry dianggap video kalau punya 'formats' atau 'url' dan bukan foto
    # yt-dlp menandai foto dengan ext 'jpg'/'jpeg'/'png' atau tidak punya formats
    video_entries = []
    for e in entries:
        ext = e.get("ext", "")
        formats = e.get("formats") or []
        has_video_format = any(
            f.get("vcodec", "none") not in ("none", "") or f.get("ext") not in ("jpg", "jpeg", "png", "webp", "")
            for f in formats
        )
        # Entry tanpa formats tapi punya url — cek ext-nya
        if not formats and e.get("url"):
            has_video_format = ext not in ("jpg", "jpeg", "png", "webp")

        if has_video_format or (not formats and ext not in ("jpg", "jpeg", "png", "webp", "")):
            video_entries.append(e)

    if not video_entries:
        # Fallback: tidak bisa filter, pakai index mentah
        idx = min(img_index - 1, len(entries) - 1)
        return entries[idx]

    # img_index adalah 1-based dari sisi user/Instagram
    idx = min(img_index - 1, len(video_entries) - 1)
    return video_entries[idx]


def fetch_ig_metadata(url: str) -> dict:
    img_index = _parse_img_index(url)
    # Fetch seluruh carousel supaya kita bisa filter entry video sendiri
    clean_url = _strip_img_index(url) if img_index else url

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        # Fetch semua entries tapi jangan error kalau ada foto
        "ignoreerrors": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            info = _pick_entry(info, img_index)

            description = info.get("description", "")

            uploader_id = _extract_username_from_url(info.get("uploader_url", ""))

            if not uploader_id:
                raw = info.get("uploader_id", "")
                if raw and not str(raw).isdigit() and " " not in str(raw):
                    uploader_id = str(raw).lstrip("@")

            if not uploader_id:
                raw = info.get("channel", "")
                if raw and not str(raw).isdigit() and " " not in str(raw):
                    uploader_id = str(raw).lstrip("@")

            if not uploader_id:
                uploader_id = _extract_username_from_url(info.get("channel_url", ""))

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
    clean_url = _strip_img_index(url) if img_index else url

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": os.path.join(output_dir, "video_%(id)s.%(ext)s"),
        "format": "mp4/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        # Download semua entry, biar kita pilih sendiri setelah selesai
        # ignoreerrors supaya foto di carousel tidak crash proses
        "ignoreerrors": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            target = _pick_entry(info, img_index)

            filename = ydl.prepare_filename(target)
            if not filename.endswith(".mp4"):
                filename = os.path.splitext(filename)[0] + ".mp4"

            if os.path.exists(filename):
                return filename

            # Fallback: scan output_dir, ambil file mp4 yang paling baru
            mp4_files = [
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.endswith(".mp4")
            ]
            if mp4_files:
                return max(mp4_files, key=os.path.getmtime)

            raise RuntimeError("File MP4 tidak ditemukan setelah download.")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to download video: {str(e)}")
