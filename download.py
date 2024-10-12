from pathlib import Path
import subprocess
import sys
import yt_dlp
from yt_dlp.utils import sanitize_filename

YDL_OPTS = {
    'format': 'bestvideo[height<=2160]+bestaudio/best',
    'merge_output_format': 'mkv',
    'outtmpl': '/tmp/newsboat/%(uploader)s/%(title)s.%(ext)s',
}


def get_file_paths(info: dict[str, str]) -> tuple[Path, Path]:
    file_name = sanitize_filename(f'{info["title"]}.{info["ext"]}')
    dir_name = sanitize_filename(info['uploader'])
    temp_path = Path('/tmp/newsboat') / dir_name / file_name
    file_path = Path.home() / 'Videos' / 'newsboat' / dir_name / file_name
    return (temp_path, file_path)


# TODO: add link to file for download complete notification
def send_notif(title: str, msg: str) -> None:
    subprocess.run(['notify-send', '--hint=int:transient:1',
                    '--urgency=normal', title, msg])


def set_url_prop(in_path: Path, out_path: Path, url: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'ffmpeg',
        '-i', in_path,
        '-metadata', f'URL="{url}"',
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
        info = ydl.extract_info(url, download=False)
        if info is None:
            send_notif('Error', f'Could not resolve URL: {url}')
            sys.exit(1)
        title = info['title'] 
        temp_path, file_path = get_file_paths(info)
        if file_path.is_file():  # TODO: check using URL prop
            send_notif('Already Downloaded', title)
            return
        send_notif('Starting Download', title)
        try:
            ydl.download([url])
        except yt_dlp.DownloadError:
            send_notif('Error', f'Error while downloading video: {url}\n{info}')
            sys.exit(1)
    set_url_prop(temp_path, file_path, url)
    send_notif('Finished Download', title)


if __name__ == '__main__':
    main()
