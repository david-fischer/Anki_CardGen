from ..design_patterns.factory import CookBook
from .base import (
    AsyncDicio,
    AsyncGoogleImages,
    AsyncLinguee,
    AsyncParser,
    AsyncReverso,
    NoMatchError,
    Parser,
)
from .new_parsers import EnglishParser

parser_cookbook = CookBook()

# BASE PARSER
parser_cookbook.register("async_reverso")(AsyncReverso)
parser_cookbook.register("async_linguee")(AsyncLinguee)
parser_cookbook.register("async_dicio")(AsyncDicio)
parser_cookbook.register("async_google_images")(AsyncGoogleImages)
# NEW PARSERS
parser_cookbook.register("english_parser")(EnglishParser)
