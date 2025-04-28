import sys

from database import delete_video, get_video
from util import send_notif


def main() -> None:
    if len(sys.argv) != 2:
        print("Invalid number of arguments.", file=sys.stderr)
        print("\tFormat: <URL>", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]

    file_path, metadata = get_video(url)
    if metadata:
        delete_video(url)
        if file_path:
            file_path.unlink(missing_ok=True)
        send_notif("Deleted Video", metadata.title)
    else:
        send_notif("Failed to Delete Video", f"Video not found: {url}")


if __name__ == "__main__":
    main()
