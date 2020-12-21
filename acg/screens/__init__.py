"""Init."""
import json
import pathlib

from kivy.factory import Factory

from .history import HistoryRoot
from .queued import QueuedRoot
from .settings import SettingsRoot
from .single_word import SingleWordRoot

SCREEN_DIR = pathlib.Path(__file__).parent

with open(SCREEN_DIR / "screen_dict.json") as file:
    screen_dicts = json.load(file)

Factory.register("SettingsRoot", SettingsRoot)
Factory.register("HistoryRoot", HistoryRoot)
Factory.register("SingleWordRoot", SingleWordRoot)
Factory.register("QueuedRoot", QueuedRoot)
