"""
Contains the functions needed on the screen screen_queue.
"""

import threading
from queue import Queue

from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton

from parsers import NoMatchError
from utils import (
    clean_up,
    set_screen,
    widget_by_id,
    word_list_from_kindle,
    word_list_from_txt,
)
from words import Word

options_dict = {
    "script-text-outline": "Import from Kindle",
    "note-text": "Import from Text File",
}
"""
dict: :code:`{"icon-name":"hint text"}` for the contents of
:class:`~kivymd.uix.button.MDFloatingActionButtonSpeedDial`.
"""


def worker_single_word():
    """As long as the queue is not empty, tries to process a single word.
    Changing the states accordingly to "loading" and "ready"
    If it fails, it moves the word to the error_words list.
    """
    while not MDApp.get_running_app().queue.empty():
        word = MDApp.get_running_app().queue.get()
        MDApp.get_running_app().loading_state_dict[word] = "loading"
        try:
            local = threading.local()
            local.word = Word()
            local.word.search(word)
            MDApp.get_running_app().loading_state_dict[word] = "ready"
        except (NoMatchError, KeyError):
            MDApp.get_running_app().queue_words.remove(word)
            MDApp.get_running_app().error_words.append(word)


def start_workers(worker_fn, num):
    """Starts a number of workers in separate threads

    Args:
      worker_fn: Function to be started
      num: Number of threads/workers

    """
    workers = [threading.Thread(target=worker_fn, name="worker") for _ in range(num)]
    for worker in workers:
        worker.start()


def queue_word(word):
    """
    Adds the word to the app.queue_words list and Queue and changes state to "queued".
    Then calls :func:`start_downloading`.

    Args:
      word: Word to add to queue.
"""
    if not is_duplicate(word):
        MDApp.get_running_app().loading_state_dict[word] = "queued"
        MDApp.get_running_app().queue_words.append(word)
        MDApp.get_running_app().queue.put(word)
        start_downloading()


def start_downloading():
    """
    Downloads data for queued words:

      * Sets up Queue
      * If no worker is present, starts one.
    """
    MDApp.get_running_app().setup_queue()
    if "worker" not in [thread.name for thread in threading.enumerate()]:
        print("starting a worker")
        start_workers(worker_single_word, 1)
    else:
        print(threading.enumerate())


def pause_downloading():
    """
    Empties queue.

    This leads the download to stop after the current word is processed.
    """
    MDApp.get_running_app().queue = Queue()


def is_duplicate(word):
    """
    Checks if word is already queued, done or has caused an error.

    Args:
      word: Word to check.

    Returns:
      :``True`` if ``word`` is already in app.queue_words, app.error_words or app.done_words.
      Else ``False``.
    """
    app = MDApp.get_running_app()
    list_names = ["queue_words", "error_words", "done_words"]
    for name in list_names:
        if word in getattr(app, name):
            print(f'"{word}" is already in {name}. Skipping.')
            return True
    return False


def choose_file_to_import(button):
    """
    Opens an instance of :class:`~kivymd.uix.filemanager.MDFileManager` so the user can choose a file to import.

    Binds function to clicking on file, so the import is started in separate thread.
    """
    button.parent.close_stack()
    text = options_dict[button.icon]
    if text == "Import from Kindle":
        extensions = [".html"]
        import_function = lambda path: start_workers(
            import_from(path, source="kindle"), 1
        )
    else:  # elif text == "Import from Text File":
        extensions = [".txt"]
        import_function = lambda path: start_workers(import_from(path, source="txt"), 1)
    MDApp.get_running_app().open_file_manager(
        ext=extensions, path="..", select_path=import_function
    )


def click_on_queue_item(item):
    """Switch to screen_single_word to generate a card for the clicked word."""
    print(item.text)
    # MDApp.get_running_app().queue_words.remove(item.text)
    set_screen("screen_single_word")
    widget_by_id("screen_single_word/word_prop/search_field").text = item.text
    widget_by_id("screen_single_word/word_prop").load_or_search(item.text)
    # MDApp.get_running_app().done_words.append(item.text)


def click_on_done_item(item):
    """Placeholder for later implementation."""
    print(item.text)


def click_on_error_item(item):
    """Placeholder for later implementation."""
    print(item.text)


def import_from(path, source="kindle"):
    """
    Imports, processes and queues words from file.

    If non-dictionary forms are detected, prompts the user with suggestions for replacement.

    Args:
      path: Path to file.
      source: Type of source. Options=["kindle","txt"] (Default value = "kindle")
    """
    MDApp.get_running_app().file_manager.close()
    import_function_dict = {"kindle": word_list_from_kindle, "txt": word_list_from_txt}
    words = import_function_dict[source](path)
    words = clean_up(words, lemmatize=False, remove_punct=True, lower_case=True)
    lemmas = clean_up(words, lemmatize=True, remove_punct=False, lower_case=False)
    suggested_replacements = [
        f"{old} -> {new}" for old, new in zip(words, lemmas) if old != new
    ]
    unchanged_words = [word for word, lemma in zip(words, lemmas) if word == lemma]
    choose_replacements_dialog(replacements=suggested_replacements)
    for word in unchanged_words:
        queue_word(word)


def choose_replacements_dialog(replacements):
    """
    Displays possible replacements.

    Opens an :class:`~kivymd.uix.dialog.MDDialog` to show possible suggestions for detected non-dictionary forms of
    words.
    """

    def item_function(obj):
        word = obj.text.split(" -> ")[-1]
        queue_word(word)
        obj.parent.remove_widget(obj)

    def button_function(_):
        for item in MDApp.get_running_app().dialog.ids.box_items.children:
            word = item.text.split(" -> ")[0]
            queue_word(word)
        MDApp.get_running_app().dialog.dismiss()

    ok_button = MDFlatButton(
        text="OK",
        text_color=MDApp.get_running_app().theme_cls.primary_color,
        on_press=button_function,
    )
    MDApp.get_running_app().show_dialog(
        message="Some words are not in their dictionary form. The following replacements are suggested:",
        options=replacements,
        item_callback=item_function,
        buttons=[ok_button],
    )
