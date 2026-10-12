"""
Auto-save and restore queue to/from Dropbox as JSON.
Called every time a pin is added or removed.
"""
import json
import dropbox
import dropbox.files


def _get_client(token="", app_key="", app_secret="", refresh_token=""):
    if refresh_token and app_key and app_secret:
        return dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
        )
    return dropbox.Dropbox(token)


def autosave_queue(pins: list, session_folder: str, cta_counter: int,
                   token="", app_key="", app_secret="", refresh_token="") -> str:
    """Save current queue to Dropbox as JSON. Returns dropbox path."""
    dbx = _get_client(token, app_key, app_secret, refresh_token)
    folder = session_folder.rstrip("/")
    path = f"{folder}/queue_backup.json"
    if not path.startswith("/"):
        path = "/" + path

    payload = {
        "session_folder": session_folder,
        "cta_counter": cta_counter,
        "pins": pins,
    }
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    dbx.files_upload(data, path, mode=dropbox.files.WriteMode.overwrite)
    return path


def list_backups(token="", app_key="", app_secret="", refresh_token="") -> list:
    """
    List all queue_backup.json files in the App Folder.
    Returns list of dicts: {path, session_folder, modified}
    """
    dbx = _get_client(token, app_key, app_secret, refresh_token)
    results = []
    try:
        res = dbx.files_search_v2("queue_backup.json")
        for match in res.matches:
            meta = match.metadata.get_metadata()
            if hasattr(meta, "path_lower") and meta.path_lower.endswith("queue_backup.json"):
                results.append({
                    "path": meta.path_display,
                    "modified": meta.server_modified.strftime("%Y-%m-%d %H:%M") if hasattr(meta, "server_modified") else "unknown",
                    "session_folder": "/".join(meta.path_display.split("/")[:-1]),
                })
    except Exception:
        pass
    return sorted(results, key=lambda x: x["modified"], reverse=True)


def restore_backup(dropbox_path: str, token="", app_key="", app_secret="", refresh_token="") -> dict:
    """Download and parse a queue backup JSON. Returns dict with pins, session_folder, cta_counter."""
    dbx = _get_client(token, app_key, app_secret, refresh_token)
    _, res = dbx.files_download(dropbox_path)
    return json.loads(res.content.decode("utf-8"))


def delete_backup(dropbox_path: str, token="", app_key="", app_secret="", refresh_token=""):
    """Delete a backup file after successful restore."""
    dbx = _get_client(token, app_key, app_secret, refresh_token)
    try:
        dbx.files_delete_v2(dropbox_path)
    except Exception:
        pass
