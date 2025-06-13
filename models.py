from dataclasses import dataclass
from enum import Enum, auto


@dataclass
class Metadata:
    url: str
    title: str
    artist: str


@dataclass
class NewsboatItem:
    url: str
    title: str
    author: str
    feed_title: str


@dataclass
class NewsboatFeed:
    url: str
    rssurl: str
    title: str


class LinkType(Enum):
    ZOOM = auto()
    MEDIASITE = auto()
    DEFAULT = auto()
