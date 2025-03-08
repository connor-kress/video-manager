from constants import DEST_DIR
from database import get_all_videos, insert_video
from util import read_metadata


def main() -> None:
    visited_urls = set[str]()
    for path in DEST_DIR.rglob('*.mkv'):
        print(path)
        metadata = read_metadata(path)
        if metadata is None:
            print(f"ERROR reading metadata: {path}")
            continue
        insert_video(path, metadata)
        visited_urls.add(metadata.url)

    videos = get_all_videos()
    for path, metadata in videos:
        if metadata.url not in visited_urls:
            print(f"Deleted: {metadata}")
            # Remove from database


if __name__ == '__main__':
    main()
