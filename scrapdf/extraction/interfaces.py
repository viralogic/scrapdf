from dataclasses import dataclass


@dataclass
class PageText(object):
    page: int
    text: str
