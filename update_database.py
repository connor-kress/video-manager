from constants import VIDEOS_DIR
from database import get_all_videos, insert_video
from util import read_metadata


def main() -> None:
    visited_urls = set[str]()
    for path in VIDEOS_DIR.rglob("*.mkv"):
        print(path)
        metadata = read_metadata(path)
        if metadata is None:
            print(f"ERROR reading metadata: {path}")
            continue
        # TODO: check if it moved before inserting it
        insert_video(path, metadata)
        visited_urls.add(metadata.url)

    videos = get_all_videos()
    for path, metadata in videos:
        if metadata.url not in visited_urls:
            print(f"Deleted: {metadata}")
            # TODO: Remove from database


if __name__ == "__main__":
    main()
