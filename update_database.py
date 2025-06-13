# from constants import VIDEOS_DIR
from database import delete_video, get_all_videos
from util import is_empty_dir
# from util import read_metadata


def prune_deleted_video_entries() -> None:
    for path, metadata in get_all_videos():
        if not path.is_file():
            print(f"Deleting entry: {metadata.artist} - {metadata.title}")
            delete_video(metadata.url)
            if is_empty_dir(path.parent):
                path.parent.rmdir()


def main() -> None:
    prune_deleted_video_entries()

    # visited_urls = set[str]()
    # for path in VIDEOS_DIR.rglob("*.mkv"):
    #     print(path)
    #     metadata = read_metadata(path)
    #     if metadata is None:
    #         print(f"ERROR reading metadata: {path}")
    #         continue
    #     # TODO: check if it moved before inserting it
    #     # insert_video(path, metadata)
    #     visited_urls.add(metadata.url)


if __name__ == "__main__":
    main()
