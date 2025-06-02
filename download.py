from enum import Enum, auto
from pathlib import Path
import re
import subprocess
import sys
import yt_dlp
from yt_dlp.utils import sanitize_filename

from config import Config, load_config
from constants import CONFIG_PATH, VIDEOS_DIR
from database import get_video, insert_video, Metadata
from mediasite import download_mediasite_video, get_mediasite_metadata
from newsboat import get_metadata_from_newsboat
from util import send_notif


class LinkType(Enum):
    ZOOM = auto()
    MEDIASITE = auto()
    DEFAULT = auto()


# def get_category_name(link_type: LinkType) -> str:
#     match link_type:
#         case LinkType.ZOOM: return "Zoom"
#         case LinkType.MEDIASITE: return "Mediasite"
#         case LinkType.DEFAULT: return "Youtube"


def get_encoding_args(link_type: LinkType, config: Config) -> list[str]:
    if link_type == LinkType.ZOOM and config.features.enable_zoom_reencoding:
        return [
            "-c:v", "libx264",
            "-c:a", "copy",
        ]
    else:
        return ["-codec", "copy"]


def get_link_type(url: str) -> LinkType:
    zoom_pattern = re.compile(r"https://([\w-]+\.)?zoom\.us/.*")
    mediasite_pattern = re.compile(r"https://mediasite\.video\.ufl\.edu/.*")
    if zoom_pattern.match(url):
        return LinkType.ZOOM
    elif mediasite_pattern.match(url):
        return LinkType.MEDIASITE
    else:
        return LinkType.DEFAULT


def set_props(
    in_path: Path,
    out_path: Path,
    metadata: Metadata,
    link_type: LinkType,
    config: Config,
) -> None:
    encoding_args = get_encoding_args(link_type, config)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg",
        "-y",  # overwrite destination file without asking
        "-i", in_path,
        "-metadata", f"URL={metadata.url}",
        "-metadata", f"title={metadata.title}",
        "-metadata", f"artist={metadata.artist}",
        *encoding_args,
        out_path,
    ], check=True)
    print(f"set url prop to {metadata.url}")


def get_file_path_from_info(info: dict[str, str], link_type: LinkType) -> Path:
    if link_type == LinkType.ZOOM:
        base_name = sanitize_filename(f'zoom-{info["id"]}')
    else:
        base_name = sanitize_filename(info["title"])
    dir_name = sanitize_filename(info.get("uploader", "Unknown"))
    file_path = VIDEOS_DIR / "Youtube" / dir_name / (base_name + ".mkv")
    return file_path


def get_temp_path(file_path: Path) -> Path:
    return file_path.with_suffix(".tmp" + file_path.suffix)


def get_metadata_with_yt_dlp(url: str) -> tuple[Path, Metadata]:
    link_type = get_link_type(url)
    with yt_dlp.YoutubeDL() as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except yt_dlp.DownloadError as e:
            send_notif("Error", f"Error downloading video: {url} {e.msg}")
            sys.exit(1)
    if info is None:
        send_notif("Error", f"Error locating video: {url}")
        sys.exit(1)
    metadata = Metadata(
        url=url,
        title = info.get("title", info.get("id", "Unknown")),
        artist = info.get("uploader", "Unknown"),
    )
    file_path = get_file_path_from_info(info, link_type)
    return file_path, metadata


def get_metadata(url: str) -> tuple[Path, Metadata]:
    link_type = get_link_type(url)
    if link_type == LinkType.MEDIASITE:
        return get_mediasite_metadata(url)

    metadata = get_metadata_from_newsboat(url)
    if metadata is None:
        return get_metadata_with_yt_dlp(url)

    dir_name = sanitize_filename(metadata.artist)
    file_name = f"{sanitize_filename(metadata.title)}.mkv"
    file_path = VIDEOS_DIR / "Youtube" / dir_name / file_name
    return file_path, metadata



def download_with_yt_dlp(metadata: Metadata, file_path: Path) -> None:
    ydl_opts = {
        "format": "bestvideo[height<=2160]+bestaudio/best",
        "merge_output_format": "mkv",
        "outtmpl": str(file_path),
        "embed-metadata": True,
        "embed-chapters": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([metadata.url])
        except yt_dlp.DownloadError as e:
            send_notif(
                "Error", f"Error downloading video: {metadata.url} {e.msg}"
            )
            sys.exit(1)


def download_video(file_path: Path, metadata: Metadata, config: Config) -> None:
    """Downloads a video with the appropriate method given the
    link type and user config.
    """
    link_type = get_link_type(metadata.url)
    if link_type == LinkType.MEDIASITE:
        download_mediasite_video(file_path, metadata)
    else:
        temp_path = get_temp_path(file_path)
        try:
            download_with_yt_dlp(metadata, temp_path)
            set_props(temp_path, file_path, metadata, link_type, config)
        except KeyboardInterrupt as err:
            temp_path.unlink(missing_ok=True)
            raise err
        temp_path.unlink()


def main() -> None:
    if len(sys.argv) != 2:
        send_notif("Error", f"Invalid arguments: {sys.argv[1:]}")
        sys.exit(1)
    url = sys.argv[1]

    file_path, metadata = get_video(url)
    if file_path is not None:
        assert metadata is not None
        send_notif("Already Downloaded", metadata.title)
        return

    config = load_config(CONFIG_PATH)
    if config is None:
        sys.exit(1)

    file_path, metadata = get_metadata(url)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    send_notif("Starting Download", metadata.title)
    try:
        download_video(file_path, metadata, config)
    except KeyboardInterrupt:
        send_notif("Canceled Download", metadata.title)
        file_path.unlink(missing_ok=True)
        sys.exit(1)

    insert_video(file_path, metadata)
    send_notif("Finished Download", metadata.title)


if __name__ == "__main__":
    main()
