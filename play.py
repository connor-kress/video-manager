import subprocess
import sys
from typing import Optional
from download import send_notif
from pathlib import Path
from pymediainfo import MediaInfo


def read_url_from_mkv(file_path: Path) -> Optional[str]:
    media_info = MediaInfo.parse(file_path)
    if isinstance(media_info, str):
        return None
    for track in media_info.tracks:
        if track.track_type == 'General':
            return track.url
    return None


def get_path_to_video(base_dir: Path, url: str) -> Optional[Path]:
    for file_path in base_dir.rglob('*.mkv'):
        file_url = read_url_from_mkv(file_path)
        print(f'{file_url=}')
        if file_url is not None and file_url == url:
            return file_path
    return None


def stream_video(url: str) -> None:
    subprocess.run(['mpv', url])


def play_file(file_path: Path) -> None:
    subprocess.run(['mpv', file_path])


def main() -> None:
    if len(sys.argv) != 2:
        send_notif('Error', f'Invalid arguments: {sys.argv[1:]}')
        sys.exit(1)
    url = sys.argv[1]
    base_dir = Path.home() / 'Videos' / 'newsboat'
    file_path = get_path_to_video(base_dir, url)
    if file_path is not None:
        # send_notif('Found video', str(file_path))
        play_file(file_path)
    else:
        # send_notif('Streaming video', url)
        stream_video(url)


if __name__ == '__main__':
    main()
