from pathlib import Path
import re
import subprocess
import sys
import yt_dlp
from yt_dlp.utils import sanitize_filename

from constants import TEMP_DIR, VIDEOS_DIR
from database import get_video, insert_video, Metadata
from util import send_notif


YDL_OPTS = {
    'format': 'bestvideo[height<=2160]+bestaudio/best',
    'merge_output_format': 'mkv',
    'outtmpl': str(TEMP_DIR / '%(uploader)s' / '%(title)s.%(ext)s'),
    'embed-metadata': True,
    'embed-chapters': True,
}


def is_zoom_link(url: str) -> bool:
    zoom_pattern = re.compile(r"https://([\w-]+\.)?zoom\.us/.*")
    return bool(zoom_pattern.match(url))


def get_file_paths(info: dict[str, str]) -> tuple[Path, Path]:
    url = info['original_url']
    if is_zoom_link(url):
        file_name = sanitize_filename(f'zoom-{info["id"]}.mkv')  # force mkv
    else:
        file_name = sanitize_filename(f'{info["title"]}.mkv')  # force mkv
    dir_name = sanitize_filename(info.get('uploader', 'Unknown'))
    temp_path = TEMP_DIR / 'Youtube' / dir_name / file_name
    file_path = VIDEOS_DIR / 'Youtube' / dir_name / file_name
    return (temp_path, file_path)


def set_props( in_path: Path, out_path: Path, metadata: Metadata) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'ffmpeg',
        '-y',  # overwrite destination file without asking
        '-i', in_path,
        '-metadata', f'URL={metadata.url}',
        '-metadata', f'title={metadata.title}',
        '-metadata', f'artist={metadata.artist}',
        '-codec', 'copy',
        out_path,
    ], check=True)
    print(f'set url prop to {metadata.url}')


def main() -> None:
    if len(sys.argv) != 2:
        send_notif('Error', f'Invalid arguments: {sys.argv[1:]}')
        sys.exit(1)
    url = sys.argv[1]
    file_path, metadata = get_video(url)
    if file_path is not None:
        assert metadata is not None
        send_notif('Already Downloaded', metadata.title)
        return

    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except yt_dlp.DownloadError as e:
            send_notif('Error', f'Error downloading video: {url} {e.msg}')
            sys.exit(1)
        if info is None:
            send_notif('Error', f'Error locating video: {url}')
            sys.exit(1)
        metadata = Metadata(
            url=url,
            title = info.get('title', info.get('id', 'Unknown')),
            artist = info.get('uploader', 'Unknown'),
        )
        temp_path, file_path = get_file_paths(info)
        ydl.params['outtmpl']['default'] = str(temp_path)
        send_notif('Starting Download', metadata.title)
        try:
            ydl.download([metadata.url])
        except yt_dlp.DownloadError as e:
            send_notif('Error', f'Error downloading video: {url} {e.msg}')
            sys.exit(1)
    set_props(temp_path, file_path, metadata)
    insert_video(file_path, metadata)
    send_notif('Finished Download', metadata.title)


if __name__ == '__main__':
    main()
