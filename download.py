from pathlib import Path
import re
import subprocess
import sys
import yt_dlp
from yt_dlp.utils import sanitize_filename

TEMP_DIR = Path.home() / 'Videos' / 'tmp_downloads'
DEST_DIR = Path.home() / 'Videos' / 'Youtube'

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
        file_name = sanitize_filename(f'{info["id"]}.mkv')  # force mkv
    else:
        file_name = sanitize_filename(f'{info["title"]}.mkv')  # force mkv
    dir_name = sanitize_filename(info.get('uploader', 'Unknown'))
    temp_path = TEMP_DIR / dir_name / file_name
    file_path = DEST_DIR / dir_name / file_name
    return (temp_path, file_path)


# TODO: add link to file for download complete notification
def send_notif(title: str, msg: str) -> None:
    subprocess.run(['notify-send', '--hint=int:transient:1',
                    '--urgency=normal', title, msg])


def set_props(
    in_path: Path, out_path: Path,
    url: str, title: str, artist: str
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'ffmpeg',
        '-i', in_path,
        '-metadata', f'URL={url}',
        '-metadata', f'title={title}',
        '-metadata', f'artist={artist}',
        '-codec', 'copy',
        out_path,
    ])
    print(f'set url prop to {url}')


def main() -> None:
    if len(sys.argv) != 2:
        send_notif('Error', f'Invalid arguments: {sys.argv[1:]}')
        sys.exit(1)
    url = sys.argv[1]
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except yt_dlp.DownloadError as e:
            send_notif('Error', f'Error downloading video: {url} {e.msg}')
            sys.exit(1)
        if info is None:
            send_notif('Error', f'Error locating video: {url}')
            sys.exit(1)
        title = info.get('title', info.get('id', 'Unknown'))
        artist = info.get('uploader', 'Unknown')
        temp_path, file_path = get_file_paths(info)
        ydl.params['outtmpl']['default'] = str(temp_path)
        if file_path.is_file():  # TODO: check using URL prop
            send_notif('Already Downloaded', title)
            return
        send_notif('Starting Download', title)
        try:
            ydl.download([url])
        except yt_dlp.DownloadError as e:
            send_notif('Error', f'Error downloading video: {url} {e.msg}')
            sys.exit(1)
    set_props(temp_path, file_path, url, title, artist)
    send_notif('Finished Download', title)


if __name__ == '__main__':
    main()
