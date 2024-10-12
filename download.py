from pathlib import Path
import subprocess
import sys
import yt_dlp
from yt_dlp.utils import sanitize_filename

YDL_OPTS = {
    'format': 'bestvideo[height<=2160]+bestaudio/best',
    'merge_output_format': 'mkv',
    'outtmpl': '~/Videos/newsboat/%(uploader)s/%(title)s.%(ext)s',
    # 'writethumbnail': True,
    # 'thumbnail_size': 'maxresdefault',
    # 'convert-thumbnail': 'jpg',
    # 'embedthumbnail': True,
    # 'postprocessor': [
    #     {
    #         'key': 'FFmpegEmbedThumbnail',
    #         'add_metadata': True,
    #         'add_thumbnail': True,
    #     },
    # ],
}


def already_downloaded(info: dict[str, str]) -> bool:
    file_name = sanitize_filename(f'{info["title"]}.{info["ext"]}')
    dir_name = sanitize_filename(info['uploader'])
    file_path = Path.home() / 'Videos' / 'newsboat' / dir_name / file_name
    return file_path.is_file()


def send_notif(title: str, msg: str) -> None:
    subprocess.run(['notify-send', '--hint=int:transient:1',
                    '--urgency=normal', title, msg])


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
        if already_downloaded(info):
            send_notif('Already Downloaded', title)
            return
        send_notif('Starting Download', title)
        try:
            ydl.download([url])
        except yt_dlp.DownloadError:
            send_notif('Error', f'Unknown error while downloading video: {url}')
            sys.exit(1)
        send_notif('Finished Download', title)


if __name__ == '__main__':
    main()
