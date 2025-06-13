import sys

from database import delete_video, get_video
from util import is_empty_dir, send_notif


def main() -> None:
    if len(sys.argv) != 2:
        print("Invalid number of arguments.", file=sys.stderr)
        print("\tFormat: <URL>", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]

    file_path, metadata = get_video(url)
    if metadata:
        if file_path:
            file_path.unlink(missing_ok=True)
            if is_empty_dir(file_path.parent):
                file_path.parent.rmdir()
        delete_video(url)
        send_notif("Deleted Video", metadata.title)
    else:
        send_notif("Failed to Delete Video", f"Video not found: {url}")


if __name__ == "__main__":
    main()
