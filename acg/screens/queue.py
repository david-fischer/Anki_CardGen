"""Contains the functions needed on the screen queue."""

import threading
from queue import Queue

from kivy.clock import Clock
from kivy.properties import DictProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from pony.orm import db_session

from ..importer import import_chain_cookbook
from ..parsers import NoMatchError
from ..utils import not_implemented_toast, set_screen, start_workers, widget_by_id


class CheckableQueue(Queue):
    """Queue with additional :meth:`__contains__` method, so one can check if item is already in queue."""

    def __contains__(self, item):
        with self.mutex:
            return item in self.queue


class QueuedRoot(FloatLayout):
    """Root widget for the queue-screen."""

    recycle_list = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty with reference to :class:`custom_widgets.scroll_widgets.RecycleList`."""
    speed_dial = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty` contains reference to
    :class:`~kivymd.uix.button.MDFloatingActionButtonSpeedDial`."""
    queue = CheckableQueue()
    """:class:`CheckableQueue` object."""
    stale = set()
    """Set of stale words, i.e. words that have been dequeued and will be skipped if appearing in the queue."""
    speed_dial_buttons = DictProperty()
    """: : :class:`~kivy.properties.DictProperty` of the form ``{"icon_name":"Help text"}``."""
    dialog = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty`. Instance of :class:`custom_widgets.dialogs.CustomDialog`."""

    def __init__(self, **kwargs):
        self.speed_dial_buttons = import_chain_cookbook.to_button_dict()
        for button_dict in self.speed_dial_buttons.values():
            button_dict["callback"].append(self.queue_words)
        super().__init__(**kwargs)
        self._init_queue()

    def _init_queue(self):
        """Queue all words in ``"queued"`` and ``"loading"`` state."""
        for word, state in MDApp.get_running_app().word_state_dict.items():
            if state in {"queued", "loading"}:
                self.queue_word(word)

    def queue_all(self, *_):
        """Queue all words that are currently in ``waiting``-state."""
        for word, state in MDApp.get_running_app().word_state_dict.items():
            if state == "waiting":
                self.queue_word(word)

    @staticmethod
    def dequeue_all(*_):
        """Placeholder-function."""
        not_implemented_toast()

    @staticmethod
    def is_duplicate(word):
        """Check if word is ``app.word_state_dict``."""
        return word in MDApp.get_running_app().word_state_dict

    def is_queued(self, word):
        """Check if word is in :attr:`queue`."""
        return word in self.queue

    def worker_single_word(self):
        """
        Take a word from app.queue and process it, changing app.loading_state_dict accordingly.

        Repeat as long as app.queue is not empty.
        """
        local = threading.local()
        local.template = MDApp.get_running_app().new_template_instance()
        while not self.queue.empty():
            word = self.queue.get()
            if word not in self.stale:
                MDApp.get_running_app().word_state_dict[word] = "loading"
                try:
                    local.template.search(word)
                    MDApp.get_running_app().word_state_dict[word] = "ready"
                except (NoMatchError, KeyError):
                    MDApp.get_running_app().word_state_dict[word] = "error"
            else:
                self.stale.remove(word)

    @staticmethod
    @db_session
    def add_waiting(word, template=None):
        """Add word in ``"waiting"`` state, waiting to be queued."""
        template = template or MDApp.get_running_app().get_current_template_db()
        if not template.get_card(word):
            template.add_card(word)
            MDApp.get_running_app().word_state_dict[word] = "waiting"

    def queue_word(self, word):
        """Queue word for downloading."""
        if not self.is_queued(word) and not self.is_duplicate(word):
            MDApp.get_running_app().word_state_dict[word] = "queued"
            self.queue.put(word)
        if word in self.stale:
            self.stale.remove(word)
        self.start_downloading()

    def queue_words(self, words):
        """Queue list of words."""
        for word in words:
            self.queue_word(word)

    def dequeue_word(self, word):
        """Change state to ``"waiting"`` and adds ``word`` to :attr:`stale` so it will be skipped in :attr:`queue`."""
        MDApp.get_running_app().word_state_dict[word] = "waiting"
        if self.is_queued(word):
            self.stale.add(word)

    def start_downloading(self, *_):
        """If no worker is present, start a new one to download data."""
        if "worker" not in [thread.name for thread in threading.enumerate()]:
            print("starting a worker")
            start_workers(self.worker_single_word, 1)

    def pause_downloading(self):
        """Empty the queue. Worker stop after finishing current task."""
        while not self.queue.empty():
            word = self.queue.get()
            MDApp.get_running_app().word_state_dict[word] = "waiting"

    @staticmethod
    def generate_card(word):
        """Switch to single_word to generate a card for the clicked word."""
        set_screen("single_word")
        Clock.schedule_once(
            lambda x: widget_by_id("single_word").template.manual_search(word)
        )

    def click_on_item(self, item):
        """Dependent of the ``current_state`` of the ``item`` performs appropriate action."""
        if item.current_state == "queued":
            self.dequeue_word(item.text)
        elif item.current_state == "ready":
            self.generate_card(item.text)
        elif item.current_state == "waiting":
            self.queue_word(item.text)

    @staticmethod
    def sort(*_):
        """Placeholder-function."""
        not_implemented_toast()

    @staticmethod
    def filter(*_):
        """Placeholder-function."""
        not_implemented_toast()
