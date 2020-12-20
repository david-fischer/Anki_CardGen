"""Init."""
import json
import os

from kivy.factory import Factory

from paths import SCREEN_DIR
from screens.history import HistoryRoot
from screens.queued import QueuedRoot
from screens.settings import SettingsRoot
from screens.single_word import SingleWordRoot

Factory.register("SingleWordRoot", SingleWordRoot)
Factory.register("QueuedRoot", QueuedRoot)
Factory.register("SettingsRoot", SettingsRoot)
Factory.register("HistoryRoot", HistoryRoot)

with open(os.path.join(SCREEN_DIR, "screen_dict.json")) as file:
    screen_dicts = json.load(file)
