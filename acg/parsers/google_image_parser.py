"""Google images parser."""
import itertools
import json
from typing import Dict

import attr
from bs4 import BeautifulSoup

from .base import AsyncParser


def traverse(nested_list, tree_types=(list, tuple)):
    """Iterate over nested list."""
    if isinstance(nested_list, tree_types):
        for value in nested_list:
            yield from traverse(value, tree_types)
    else:
        yield nested_list


@attr.s(auto_attribs=True)
class AsyncGoogleImages(AsyncParser):
    """
    New parser to implement.

    Import in parsers/__init__.py and register via
    parser_cookbook.register("some_name")(NewParser)
    """

    base_url: str = "https://www.google.com/search"
    limit: int = 20

    def request_params(self):
        """Implement if necessary."""
        return {"q": self.phrase, "tbm": "isch", "lr": f"lang_{self.from_lang}"}

    def parse_response(self, response: dict or list or str) -> Dict[str, list]:
        """Implement."""
        soup = BeautifulSoup(response, "lxml")
        answer = str(soup.body.select("script")[-3])
        # pprint(answer)
        start = answer.find("data:") + len("data:")
        stop = answer.rfind("\n")
        json_obj = json.loads(answer[start:stop])
        thumbnails = []
        images = []
        for x in json_obj[31][0][12][2]:
            try:
                thumb, image = itertools.islice(
                    filter(lambda x: isinstance(x, str) and "https" in x, traverse(x)),
                    2,
                )
                thumbnails.append(thumb)
                images.append(image)
            except ValueError:
                pass
        return {"thumbnail": images[: self.limit], "image": thumbnails[: self.limit]}
