import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
import os


def get_dropbox_client(token: str, app_key: str = "", app_secret: str = "", refresh_token: str = "") -> dropbox.Dropbox:
    """
    Return authenticated Dropbox client.
    Prefers refresh_token (permanent) over access token (expires in 4h).
    """
    if refresh_token and app_key and app_secret:
        return dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
        )
    return dropbox.Dropbox(token)


def upload_and_get_link(local_path: str, dropbox_folder: str, token: str,
                         app_key: str = "", app_secret: str = "", refresh_token: str = "") -> str:
    dbx = get_dropbox_client(token, app_key, app_secret, refresh_token)

    filename = os.path.basename(local_path)
    dropbox_path = f"{dropbox_folder.rstrip('/')}/{filename}"
    if not dropbox_path.startswith("/"):
        dropbox_path = "/" + dropbox_path

    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

    try:
        shared = dbx.sharing_create_shared_link_with_settings(dropbox_path)
        link = shared.url
    except dropbox.exceptions.ApiError:
        links = dbx.sharing_list_shared_links(path=dropbox_path, direct_only=True)
        if links.links:
            link = links.links[0].url
        else:
            raise RuntimeError("Could not create or retrieve shared link.")

    direct_link = link.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    direct_link = direct_link.replace("?dl=0", "").replace("&dl=0", "")
    if "dl=1" not in direct_link:
        sep = "&" if "?" in direct_link else "?"
        direct_link = f"{direct_link}{sep}dl=1"

    return direct_link
