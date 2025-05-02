from pathlib import Path
import sys
from typing import Any, Optional
import browser_cookie3
import requests
import subprocess

from yt_dlp.utils import sanitize_filename

from constants import VIDEOS_DIR
from database import get_video, insert_video, Metadata
from newsboat import get_metadata_from_newsboat
from util import send_notif


def get_cookie_string(domain_filter: str) -> str:
    """Extract cookies for the given domain and return them as a
    Cookie header string.
    """
    cj = browser_cookie3.firefox()
    cookies = []
    for cookie in cj:
        if domain_filter in cookie.domain:
            cookies.append(f"{cookie.name}={cookie.value}")
    return "; ".join(cookies)


def get_player_options(
    cookie_string: str, video_url: str, video_id: str
) -> dict[str, Any]:
    """Make the POST request to the GetPlayerOptions endpoint using
    the Cookie header.
    """
    url = "https://mediasite.video.ufl.edu/Mediasite/PlayerService/PlayerService.svc/json/GetPlayerOptions"
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": video_url,
        "Content-Type": "application/json",
        "Origin": "https://mediasite.video.ufl.edu",
        "DNT": "1",
        "Connection": "keep-alive",
        "Cookie": cookie_string,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "Priority": "u=0"
    }
    data = {
        "getPlayerOptionsRequest": {
            "QueryString": "",
            "ResourceId": video_id,
            "UrlReferrer": None
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def extract_mediasite_m3u8_url(json_response: dict[str, Any]) -> Optional[str]:
    """Extract the first m3u8 URL from the JSON response."""
    m3u8_mimetype = "audio/x-mpegurl"
    try:
        presentation = json_response["d"]["Presentation"]
        if presentation is None:
            print("Presentation is null in json (extracting m3u8 url)")
            return None  # might be expired auth
        for video_url in presentation["Streams"][0]["VideoUrls"]:
            if video_url.get("MimeType") == m3u8_mimetype:
                return video_url["Location"]
        return None
    except (KeyError, IndexError, TypeError) as e:
        print(f"Unable to parse json for m3u8 url: {str(e)}")
        return None


def download_m3u8(m3u8_url: str, out_path: Path, metadata: Metadata) -> None:
    """Call FFmpeg with the m3u8 URL and additional headers."""
    subprocess.run([
        "ffmpeg",
        "-y",  # overwrite destination file without asking
        "-headers", "Referer: https://mediasite.video.ufl.edu/\r\nOrigin: https://mediasite.video.ufl.edu",
        "-i", m3u8_url,
        "-metadata", f"URL={metadata.url}",
        "-metadata", f"title={metadata.title}",
        "-metadata", f"artist={metadata.artist}",
        "-c", "copy",
        str(out_path),
    ], check=True)

def download_mediasite_video(out_path: Path, metadata: Metadata) -> None:
    video_url = metadata.url
    video_id = video_url.rstrip("/").split("/")[-1]
    # Extract cookies from Firefox for the domain
    cookie_str = get_cookie_string("mediasite.video.ufl.edu")
    # print(f"{cookie_str=}")
    # Get the JSON response for player options
    json_data = get_player_options(cookie_str, video_url, video_id)
    # Extract the m3u8 URL from the JSON response
    m3u8_url = extract_mediasite_m3u8_url(json_data)

    if m3u8_url is not None:
        print("m3u8 URL found:", m3u8_url)
        download_m3u8(m3u8_url, out_path, metadata)
    else:
        print("Failed to extract m3u8 URL from JSON.")
        send_notif("Failed to extract m3u8 URL", "Do you have valid Gatorlink credentials?")
        sys.exit(1)


def get_mediasite_metadata(url: str) -> tuple[Path, Metadata]:
    metadata = get_metadata_from_newsboat(url)
    if metadata is None:
        print("Newsboat data not found")
        send_notif("Error extracting metadata", "Newsboat data not found")
        sys.exit(1)
    dir_name = sanitize_filename(metadata.artist)
    file_name = f"{sanitize_filename(metadata.title)}.mkv"
    file_path = VIDEOS_DIR / "mediasite" / dir_name / file_name
    return file_path, metadata


def main() -> None:
    if len(sys.argv) != 2:
        print("Invalid number of arguments.", file=sys.stderr)
        print("\tFormat: <URL>", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]

    _, metadata = get_video(url)
    if metadata is not None:
        send_notif("Already Downloaded", metadata.title)
        return

    out_path, metadata = get_mediasite_metadata(url)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    send_notif("Starting Download", metadata.title)
    download_mediasite_video(out_path, metadata)
    insert_video(out_path, metadata)
    send_notif("Finished Download", metadata.title)


if __name__ == "__main__":
    main()
