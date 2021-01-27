from dataclasses import dataclass
from typing import Union


@dataclass
class PageText(object):
    page: int
    text: Union[bytes, str]
