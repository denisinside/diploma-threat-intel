from .mega import download_mega
from .mediafire import download_mediafire
from .upload_ee import download_upload_ee
from .browser_downloader import download_via_browser

CLOUD_DOWNLOADERS = {
    "mega": download_mega,
    "mediafire": download_mediafire,
    "upload_ee": download_upload_ee,
}

DEFAULT_CLOUD_DOWNLOADER = download_via_browser
