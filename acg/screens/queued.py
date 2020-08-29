"""Contains the functions needed on the screen queue."""
import os
import threading
from queue import Queue

from kivy.clock import Clock
from kivy.properties import DictProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from pony.orm import db_session

from custom_widgets.dialogs import CustomDialog, ReplacementContent
from parsers import NoMatchError
from utils import (
    clean_up,
    set_screen,
    start_thread,
    start_workers,
    widget_by_id,
    word_list_from_kindle,
    word_list_from_txt,
)


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
    import_options = DictProperty(
        {
            "script-text-outline": "Import from Kindle",
            "note-text": "Import from Text File",
        }
    )
    """: : :class:`~kivy.properties.DictProperty` of the form ``{"icon_name":"Help text"}``."""
    dialog = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty`. Instance of :class:`custom_widgets.dialogs.CustomDialog`."""
    file_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(QueuedRoot, self).__init__(**kwargs)
        self._init_queue()
        self._init_dialog()

    def _init_queue(self):
        """Queue all words in ``"queued"`` and ``"loading"`` state."""
        for word, state in MDApp.get_running_app().word_state_dict.items():
            if state in ["queued", "loading"]:
                self.queue_word(word)

    def queue_all(self, *_):
        """Placeholder-function."""

    def dequeue_all(self, *_):
        """Placeholder-function."""

    def _init_dialog(self):
        """Initialize :attr:`dialog` as instance of :class:`custom_widgets.dialogs.CustomDialog`."""
        content = ReplacementContent()
        self.dialog = CustomDialog(
            title="Some words are not in their dictionary form. The following replacements are suggested:",
            content_cls=content,
            callback=self.dialog_callback,
        )

    def dialog_callback(self, btn_txt, words):
        """Add ``words`` to :attr:`queue` if ``"OK"``-button was pressed."""
        if btn_txt == "OK":
            for word in words:
                self.queue_word(word)

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
        while not self.queue.empty():
            word = self.queue.get()
            if word not in self.stale:
                MDApp.get_running_app().word_state_dict[word] = "loading"
                try:
                    local = threading.local()
                    local.template = MDApp.get_running_app().template
                    local.template.search(word)
                    MDApp.get_running_app().word_state_dict[word] = "ready"
                except (NoMatchError, KeyError):
                    MDApp.get_running_app().word_state_dict[word] = "error"
                    # MDApp.get_running_app().queue_words.remove(word)
                    # MDApp.get_running_app().error_words.append(word)
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
        MDApp.get_running_app().word_state_dict[word] = "queued"
        if not self.is_queued(word):
            self.queue.put(word)
        if word in self.stale:
            self.stale.remove(word)
        self.start_downloading()

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
        print(threading.enumerate())

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

    def choose_file_to_import(self, button):
        """
        Open an instance of :class:`~kivymd.uix.filemanager.MDFileManager` to let user choose a file to import.

        Binds function to clicking on file, so the import is started in separate thread.
        """
        self.speed_dial.close_stack()
        text = self.import_options[button.icon]
        if text == "Import from Kindle":
            extensions = [".html"]
            source = "kindle"
        else:  # elif text == "Import from Text File":
            extensions = [".txt"]
            source = "txt"
        import_function = start_thread(  # pylint: disable=no-value-for-parameter
            self.import_from, source=source, name="import_thread"
        )
        self.open_file_manager(
            ext=extensions, path="..", select_path=import_function,
        )

    def import_from(self, path, source="kindle"):
        """
        Import, process and queue words from file.

        If non-dictionary forms are detected, prompts the user with suggestions for replacement.

        Args:
          path: Path to file.
          source: Type of source. Options=["kindle","txt"] (Default value = "kindle")
        """
        MDApp.get_running_app().file_manager.close()
        import_function_dict = {
            "kindle": word_list_from_kindle,
            "txt": word_list_from_txt,
        }
        words = import_function_dict[source](path)
        words = clean_up(words, lemmatize=False, remove_punct=True, lower_case=True)
        lemmas = clean_up(words, lemmatize=True, remove_punct=False, lower_case=False)
        new_pairs = [
            (word, lemma)
            for word, lemma in zip(words, lemmas)
            if not (self.is_duplicate(word) or self.is_duplicate(lemma))
        ]
        suggested_replacements = [
            {"word": word, "lemma": lemma} for word, lemma in new_pairs if word != lemma
        ]
        unchanged_words = [word for word, lemma in new_pairs if word == lemma]
        print(unchanged_words, suggested_replacements)
        self.show_replacements_dialog(replacements=suggested_replacements)
        for word in unchanged_words:
            self.add_waiting(word)

    def show_replacements_dialog(self, replacements):
        """Open dialog to show user possible corrections for the imported words."""
        self.dialog.content_cls.data = [
            {**rep_dict, "height": 45} for rep_dict in replacements
        ]
        self.dialog.open()

    def open_file_manager(self, path=None, select_path=print, ext=None):
        """Open file manager at :attr:`path` and calls :attr:`select_path` with path of selected file."""
        path = path or "."
        path = os.path.abspath(path)
        if not self.file_manager:
            self.file_manager = MDFileManager()
        ext = ext or [".html"]
        self.file_manager.ext = ext
        self.file_manager.select_path = select_path
        self.file_manager.show(path)
