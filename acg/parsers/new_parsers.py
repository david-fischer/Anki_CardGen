"""Some new parsers."""

from typing import Dict

from .base import AsyncParser


class NewParser(AsyncParser):
    """
    New parser to implement.

    Import in parsers/__init__.py and register via
    parser_cookbook.register("some_name")(NewParser)
    """

    def request_params(self):
        """Implement if necessary."""

    def parse_response(self, response: dict or list or str) -> Dict[str, list]:
        """Implement."""
