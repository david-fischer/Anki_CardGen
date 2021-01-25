"""Some new parsers."""
from typing import Dict

import attr
from bs4 import BeautifulSoup

from .base import AsyncParser


@attr.s(auto_attribs=True)
class EnglishParser(AsyncParser):
    """
    New parser to implement.

    Import in parsers/__init__.py and register via
    parser_cookbook.register("some_name")(NewParser)
    """

    base_url: str = "https://dictionary.cambridge.org/de/worterbuch/englisch/{phrase}"

    # def request_params(self):
    #     """Implement if necessary."""

    def parse_response(self, response: dict or list or str) -> Dict[str, list]:
        """Implement."""
        soup = BeautifulSoup(response, "html.parser")
        definitions = soup.find_all("div", class_="def ddef_d db")
        synonyms = soup.find_all("span", class_="x-h dx-h")
        examples = soup.find_all("span", class_="deg")
        return {
            "explanation": [d.get_text()[:-2] for d in definitions],
            "explanation_trans": [None for _ in definitions],
            "example": [ex.get_text().strip() for ex in examples],
            "example_trans": [None for _ in examples],
            "synonym_trans": [None for _ in synonyms],
            "synonym": [s.get_text() for s in synonyms],
        }
