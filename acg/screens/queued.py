"""Contains the functions needed on the screen queue."""
import threading
from queue import Queue

from kivy.clock import Clock
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from pony.orm import db_session

from custom_widgets.dialogs import CustomDialog, ReplacementItemsContent
from parsers import NoMatchError
from utils import (
    clean_up,
    not_implemented_toast,
    set_screen,
    start_thread,
    start_workers,
    widget_by_id,
    word_list_from_kindle,
    word_list_from_kobo,
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
    import_dicts = ListProperty(
        [
            {
                "icon": "book-open",
                "text": "Import from Kindle",
                "exts": [".html"],
                "import_fn": word_list_from_kindle,
                "import_dir": MDApp.get_running_app().getter("import_dir"),
            },
            {
                "icon": "book-open-variant",
                "text": "Import from Kobo Annotations",
                "exts": [".annot"],
                "import_fn": word_list_from_kobo,
                "import_dir": MDApp.get_running_app().getter("kobo_import_dir"),
            },
            {
                "icon": "note-text",
                "text": "Import from txt-file",
                "exts": [".txt"],
                "import_fn": word_list_from_txt,
                "import_dir": MDApp.get_running_app().getter("import_dir"),
            },
        ]
    )
    """: : :class:`~kivy.properties.DictProperty` of the form ``{"icon_name":"Help text"}``."""
    dialog = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty`. Instance of :class:`custom_widgets.dialogs.CustomDialog`."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_queue()
        self._init_dialog()

    def _init_queue(self):
        """Queue all words in ``"queued"`` and ``"loading"`` state."""
        for word, state in MDApp.get_running_app().word_state_dict.items():
            if state in ["queued", "loading"]:
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

    def _init_dialog(self):
        """Initialize :attr:`dialog` as instance of :class:`custom_widgets.dialogs.CustomDialog`."""
        content = ReplacementItemsContent()
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
        import_dict = [
            imp_dict
            for imp_dict in self.import_dicts
            if imp_dict["icon"] == button.icon
        ][0]
        print(import_dict["import_dir"])
        import_function = start_thread(  # pylint: disable=no-value-for-parameter
            self.import_from, import_fn=import_dict["import_fn"], name="import_thread"
        )
        app = MDApp.get_running_app()
        app.open_file_manager(
            ext=import_dict["exts"],
            path=import_dict["import_dir"](self),
            callback=import_function,
        )

    def import_from(self, path, import_fn=word_list_from_kindle):
        """
        Import, process and queue words from file.

        If non-dictionary forms are detected, prompts the user with suggestions for replacement.

        Args:
          path: Path to file.
          import_fn: function that returns list of words
        """
        MDApp.get_running_app().file_manager.close()
        words = import_fn(path)
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
        self.show_replacements_dialog(replacements=suggested_replacements)
        for word in unchanged_words:
            self.add_waiting(word)

    def show_replacements_dialog(self, replacements):
        """Open dialog to show user possible corrections for the imported words."""
        self.dialog.content_cls.data = [
            {**rep_dict, "height": 45} for rep_dict in replacements
        ]
        self.dialog.open()

    @staticmethod
    def sort(*_):
        """Placeholder-function."""
        not_implemented_toast()

    @staticmethod
    def filter(*_):
        """Placeholder-function."""
        not_implemented_toast()
