import threading
from functools import partial

from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton

from utils import clean_up, word_list_from_kindle
from word_requests.pt_word import Word
from word_requests.urls_and_parsers import NoMatchError

options_dict = {
    "script-text-outline": "Import from Kindle",
    "note-text":           "Import from Text File"
}


def worker_single_word():
    """
    As long as the queue is not empty, tries to process a single word.
    Changing the states accordingly to "loading" and "ready"
    If it fails, it moves the word to the error_words list.
    """
    while not MDApp.get_running_app().q.empty():
        word = MDApp.get_running_app().q.get()
        MDApp.get_running_app().loading_state_dict[word] = "loading"
        try:
            local = threading.local()
            local.word = Word()
            local.word.search(word)
            MDApp.get_running_app().loading_state_dict[word] = "ready"
        except (NoMatchError, KeyError):
            MDApp.get_running_app().queue_words.remove(word)
            MDApp.get_running_app().error_words.append(word)


def start_workers(worker, num):
    """
    Starts a number of workers in seperate threads
    :param worker: function to be started
    :param num:
    """
    workers = [threading.Thread(target=worker, name="worker") for _ in range(num)]
    for w in workers:
        w.start()


def queue_word(word):
    """
    Adds the word to the app.queue_words list and Queue and changes state to "queued".
    If no worker is present starts a worker in a different thread.
    :param word:
    """
    if not is_duplicate(word):
        MDApp.get_running_app().loading_state_dict[word] = "queued"
        MDApp.get_running_app().queue_words.append(word)
        MDApp.get_running_app().q.put(word)
        if "worker" not in [thread.name for thread in threading.enumerate()]:
            start_workers(worker_single_word, 1)


def is_duplicate(word):
    app = MDApp.get_running_app()
    list_names = ["queue_words", "error_words", "done_words"]
    for name in list_names:
        if word in getattr(app, name):
            print(f"\"{word}\" is already in {name}. Skipping.")
            return True
    return False

def import_from(button):
    button.parent.close_stack()
    text = options_dict[button.icon]
    if text == "Import from Kindle":
        MDApp.get_running_app().open_file_manager(
            ext=[".html"],
            path="./test/test_data/",
            select_path=lambda path: threading.Thread(target=partial(import_from_kindle, path)).start()
        )
    elif text == "Import from Text File":
        print("Importing from text-file...")


def click_on_queue_item(item):
    print(item.text)
    MDApp.get_running_app().queue_words.remove(item.text)
    MDApp.get_running_app().done_words.append(item.text)


def click_on_done_item(item):
    print(item.text)


def click_on_error_item(item):
    print(item.text)


def import_from_kindle(path):
    print("Importing from kindle-html-file...")
    MDApp.get_running_app().file_manager.close()
    words = clean_up(word_list_from_kindle(path), lemmatize=False)
    lemmas = clean_up(words)
    suggested_replacements = [f"{old} -> {new}" for old, new in zip(words, lemmas) if old != new]
    unchanged_words = [word for word, lemma in zip(words, lemmas) if word == lemma]
    for word in unchanged_words:
        queue_word(word)
    choose_replacements_dialog(
        replacements=suggested_replacements)


def choose_replacements_dialog(replacements):
    def item_function(obj):
        word = obj.text.split(" -> ")[-1]
        queue_word(word)
        obj.parent.remove_widget(obj)

    def button_function(obj):
        for item in MDApp.get_running_app().dialog.ids.box_items.children:
            word = item.text.split(" -> ")[0]
            queue_word(word)
        MDApp.get_running_app().dialog.dismiss()

    ok_button = MDFlatButton(
        text="OK",
        text_color=MDApp.get_running_app().theme_cls.primary_color,
        on_press=button_function
    )
    MDApp.get_running_app().show_dialog(
        message="Some words are not in their dictionary form. The following replacements are suggested:",
        options=replacements,
        callback=print,
        item_function=item_function,
        buttons=[ok_button]
    )
