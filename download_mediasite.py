from pathlib import Path
import sys
from typing import Any, Optional
import browser_cookie3
import requests
import subprocess

from util import send_notif


def get_cookie_string(domain_filter: str) -> str:
    """Extract cookies for the given domain and return them as a
    Cookie header string.
    """
    cj = browser_cookie3.firefox()
    cookies = []
    for cookie in cj:
        if domain_filter in cookie.domain:
            cookies.append(f'{cookie.name}={cookie.value}')
    return '; '.join(cookies)


def get_player_options(
    cookie_string: str, video_url: str, video_id: str
) -> dict[str, Any]:
    """Make the POST request to the GetPlayerOptions endpoint using
    the Cookie header.
    """
    url = 'https://mediasite.video.ufl.edu/Mediasite/PlayerService/PlayerService.svc/json/GetPlayerOptions'
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': video_url,
        'Content-Type': 'application/json',
        'Origin': 'https://mediasite.video.ufl.edu',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Cookie': cookie_string,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'Priority': 'u=0'
    }
    data = {
        'getPlayerOptionsRequest': {
            'QueryString': '',
            'ResourceId': video_id,
            'UrlReferrer': None
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def extract_mediasite_m3u8_url(json_response: dict[str, Any]) -> Optional[str]:
    """Extract the first m3u8 URL from the JSON response."""
    try:
        presentation = json_response['d']['Presentation']
        if presentation is None:
            print('Presentation is null in json (extracting m3u8 url)')
            return None  # might be expired auth
        return presentation['Streams'][0]['VideoUrls'][0]['Location']
    except (KeyError, IndexError, TypeError) as e:
        print(f'Unable to parse json for m3u8 url: {str(e)}')
        return None


def download_m3u8(m3u8_url: str, out_path: Path) -> None:
    """Call FFmpeg with the m3u8 URL and additional headers."""
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # overwrite destination file without asking
        '-headers', 'Referer: https://mediasite.video.ufl.edu/\r\nOrigin: https://mediasite.video.ufl.edu',
        '-i', m3u8_url,
        '-c', 'copy',
        str(out_path),
    ]
    subprocess.run(ffmpeg_cmd, check=True)

def download_mediasite_video(video_url: str, out_path: Path) -> None:
    video_id = video_url.rstrip('/').split('/')[-1]
    # Extract cookies from Firefox for the domain
    cookie_str = get_cookie_string('mediasite.video.ufl.edu')
    # print(f'{cookie_str=}')
    # Get the JSON response for player options
    json_data = get_player_options(cookie_str, video_url, video_id)
    # Extract the m3u8 URL from the JSON response
    m3u8_url = extract_mediasite_m3u8_url(json_data)

    if m3u8_url is not None:
        print('m3u8 URL found:', m3u8_url)
        # Optionally, download the video with FFmpeg:
        send_notif('Starting Download', video_url)
        download_m3u8(m3u8_url, out_path)
        send_notif('Finished Download', video_url)
    else:
        print('Failed to extract m3u8 URL from JSON.')
        send_notif('Failed to extract m3u8 URL', 'Do you have valid Gatorlink credentials?')


def main() -> None:
    # video_url = 'https://mediasite.video.ufl.edu/Mediasite/Play/2d38a508c97546cdadd9d5beeb9411dc1d'
    video_url = sys.argv[1]
    out_path = Path(sys.argv[2])
    download_mediasite_video(video_url, out_path)


if __name__ == '__main__':
    main()
