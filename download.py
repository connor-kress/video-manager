from pathlib import Path
import subprocess
import sys
import yt_dlp
from yt_dlp.utils import sanitize_filename

from config import Config, load_config
from constants import CONFIG_PATH, VIDEOS_DIR
from database import clear_reservation, get_video, insert_video, try_reserve_url
from mediasite import download_mediasite_video, get_mediasite_metadata
from models import LinkType, Metadata
from newsboat import (
    fetch_newsboat_feed_and_items,
    get_metadata_from_newsboat,
)
from util import get_link_type, read_urls_from_file, send_notif


def get_encoding_args(link_type: LinkType, config: Config) -> list[str]:
    if link_type == LinkType.ZOOM and config.features.zoom_reencoding:
        return [
            "-codec:v", "libx264",
            "-codec:a", "copy",
        ]
    else:
        return ["-codec", "copy"]


def set_props(
    in_path: Path,
    out_path: Path,
    metadata: Metadata,
    link_type: LinkType,
    config: Config,
) -> None:
    encoding_args = get_encoding_args(link_type, config)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run([
            "ffmpeg",
            "-y",  # overwrite destination file without asking
            "-i", in_path,
            "-metadata", f"URL={metadata.url}",
            "-metadata", f"title={metadata.title}",
            "-metadata", f"artist={metadata.artist}",
            *encoding_args,
            out_path,
        ], check=False)
    except subprocess.CalledProcessError as e:
        err_msg = str(e) if e.stderr is None else e.stderr.decode()
        send_notif(
            "Error", f"Error setting video props: {metadata.title} {err_msg}"
        )
        sys.exit(1)
    except FileNotFoundError as e:
        send_notif(
            "Error", f"Error downloading video: {metadata.title} {e}"
        )
        sys.exit(1)
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


def get_metadata(url: str, config: Config) -> tuple[Path, Metadata]:
    is_mediasite = get_link_type(url) == LinkType.MEDIASITE
    if is_mediasite and config.features.custom_mediasite_handler:
        return get_mediasite_metadata(url)

    metadata = get_metadata_from_newsboat(url)
    if metadata is None:
        return get_metadata_with_yt_dlp(url)

    dir_name = sanitize_filename(metadata.artist)
    file_name = f"{sanitize_filename(metadata.title)}.mkv"
    file_path = VIDEOS_DIR / "Youtube" / dir_name / file_name
    return file_path, metadata



def download_with_yt_dlp_lib(metadata: Metadata, file_path: Path) -> None:
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


def download_with_yt_dlp_cli(
    metadata: Metadata,
    file_path: Path,
    config: Config,
) -> None:
    try:
        subprocess.run([
            config.download.yt_dlp_path,
            "-f", "bestvideo[height<=2160]+bestaudio/best",
            "--merge-output-format", "mkv",
            "-o", file_path,
            metadata.url,
        ], check=False) # check=True with exit when any stderr is encountered
    except subprocess.CalledProcessError as e:
        err_msg = str(e) if e.stderr is None else e.stderr.decode()
        send_notif(
            "Error", f"Error downloading video: {metadata.title} {err_msg}"
        )
        sys.exit(1)
    except FileNotFoundError as e:
        send_notif(
            "Error", f"Error downloading video: {metadata.title} {e}"
        )
        sys.exit(1)


def download_video(file_path: Path, metadata: Metadata, config: Config) -> None:
    """Downloads a video with the appropriate method given the
    link type and user config.
    """
    link_type = get_link_type(metadata.url)
    is_mediasite = link_type == LinkType.MEDIASITE
    if is_mediasite and config.features.custom_mediasite_handler:
        download_mediasite_video(file_path, metadata)
    else:
        temp_path = get_temp_path(file_path)
        try:
            if config.download.use_yt_dlp_cli:
                download_with_yt_dlp_cli(metadata, temp_path, config)
            else:
                download_with_yt_dlp_lib(metadata, temp_path)
            set_props(temp_path, file_path, metadata, link_type, config)
        except KeyboardInterrupt as err:
            temp_path.unlink(missing_ok=True)
            raise err
        temp_path.unlink()


def handle_single_download(url: str, config: Config) -> None:
    file_path, metadata = get_video(url)
    if file_path is not None:
        assert metadata is not None
        send_notif("Already Downloaded", metadata.title)
        return

    file_path, metadata = get_metadata(url, config)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not try_reserve_url(url):
        send_notif("Download Already In-Progress", metadata.title)
        return

    send_notif("Starting Download", metadata.title)
    try:
        download_video(file_path, metadata, config)
    except KeyboardInterrupt:
        send_notif("Canceled Download", metadata.title)
        file_path.unlink(missing_ok=True)
        sys.exit(1)

    insert_video(file_path, metadata)
    clear_reservation(url)
    send_notif("Finished Download", metadata.title)


def handle_bulk_feed_download(
    feed_url: str,
    config: Config,
    only_unread: bool,
) -> None:
    feed, all_items = fetch_newsboat_feed_and_items(feed_url)
    if feed is None:
        send_notif("Error", f"Could not find feed: {feed_url}")
        sys.exit(1)

    items = []
    for item in all_items:
        file_path, _ = get_video(item.url)
        if file_path is not None:
            continue
        if item.unread or not only_unread:
            items.append(item)

    if len(items) == 0:
        send_notif("All Downloaded", f"{feed.title} ({len(all_items)} videos)")
        sys.exit(1)

    send_notif("Starting Bulk Download", f"{feed.title} ({len(items)} videos)")
    skipped = 0
    for i, item in enumerate(items):
        file_path, metadata = get_metadata(item.url, config)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not try_reserve_url(metadata.url):
            print(f"\nSkipping: {item.title} ({i+1}/{len(items)})")
            skipped += 1
            continue
        print(f"\nDownloading: {item.title} ({i+1}/{len(items)})\n")
        try:
            download_video(file_path, metadata, config)
        except KeyboardInterrupt:
            rem = len(items) - i
            send_notif(
                "Canceled Bulk Download",
                f"{feed.title} {rem}/{len(items)} remaining",
            )
            file_path.unlink(missing_ok=True)
            sys.exit(1)
        insert_video(file_path, metadata)
        clear_reservation(metadata.url)

    downloaded = len(items) - skipped
    if skipped == 0:
        msg = f"{feed.title} ({downloaded} downloaded)"
    else:
        msg = f"{feed.title} ({downloaded} downloaded, {skipped} skipped)"
    send_notif("Finished Bulk Download", msg)


def handle_bulk_file_download(list_path: Path, config: Config) -> None:
    all_urls = read_urls_from_file(list_path)
    if all_urls is None:
        sys.exit(1)

    urls = []
    for url in all_urls:
        file_path, _ = get_video(url)
        if file_path is None:
            urls.append(url)

    if len(urls) == 0:
        send_notif("All Downloaded", f"{list_path} ({len(urls)} videos)")
        sys.exit(1)

    send_notif("Starting Bulk Download", f"{list_path} ({len(urls)} videos)")
    skipped = 0
    for i, url in enumerate(urls):
        file_path, metadata = get_metadata(url, config)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not try_reserve_url(metadata.url):
            print(f"\nSkipping: {url} ({i+1}/{len(urls)})")
            skipped += 1
            continue
        print(f"\nDownloading: {url} ({i+1}/{len(urls)})\n")
        try:
            download_video(file_path, metadata, config)
        except KeyboardInterrupt:
            rem = len(urls) - i
            send_notif("Canceled Bulk Download", f"{rem}/{len(urls)} remaining")
            file_path.unlink(missing_ok=True)
            sys.exit(1)
        insert_video(file_path, metadata)
        clear_reservation(metadata.url)

    downloaded = len(urls) - skipped
    if skipped == 0:
        msg = f"{list_path} ({downloaded} downloaded)"
    else:
        msg = f"{list_path} ({downloaded} downloaded, {skipped} skipped)"
    send_notif("Finished Bulk Download", msg)


def main() -> None:
    config = load_config(CONFIG_PATH)
    if config is None:
        sys.exit(1)

    if len(sys.argv) == 2:
        url = sys.argv[1]
        handle_single_download(url, config)
    elif len(sys.argv) == 3 and sys.argv[1] == "--file":
        file_path = Path(sys.argv[2])
        handle_bulk_file_download(file_path, config)
    elif len(sys.argv) == 3 and sys.argv[1] == "--feed":
        feed_url = sys.argv[2]
        handle_bulk_feed_download(feed_url, config, only_unread=True)
    elif len(sys.argv) == 4 and sys.argv[1] == "--feed" and sys.argv[2] == "--all":
        feed_url = sys.argv[3]
        handle_bulk_feed_download(feed_url, config, only_unread=False)
    else:
        send_notif("Error", f"Invalid Arguments: {sys.argv[1:]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
