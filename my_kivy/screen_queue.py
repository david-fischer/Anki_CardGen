import threading
from queue import Queue

from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton

from utils import (
    clean_up,
    set_screen,
    widget_by_id,
    word_list_from_kindle,
    word_list_from_txt,
)
from word_requests.pt_word import Word
from word_requests.urls_and_parsers import NoMatchError

options_dict = {
    "script-text-outline": "Import from Kindle",
    "note-text": "Import from Text File",
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
        start_downloading()


def start_downloading():
    MDApp.get_running_app().setup_queue()
    if "worker" not in [thread.name for thread in threading.enumerate()]:
        print("starting a worker")
        start_workers(worker_single_word, 1)
    else:
        print(threading.enumerate())


def pause_downloading():
    MDApp.get_running_app().q = Queue()


def is_duplicate(word):
    app = MDApp.get_running_app()
    list_names = ["queue_words", "error_words", "done_words"]
    for name in list_names:
        if word in getattr(app, name):
            print(f'"{word}" is already in {name}. Skipping.')
            return True
    return False


def choose_file_to_import(button):
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
        ext=extensions, path="./test/test_data/", select_path=import_function
    )


def click_on_queue_item(item):
    print(item.text)
    # MDApp.get_running_app().queue_words.remove(item.text)
    set_screen("screen_single_word")
    widget_by_id("screen_single_word/edit_tab/word_prop/search_field").text = item.text
    widget_by_id("screen_single_word/edit_tab/word_prop").load_or_search(item.text)
    # MDApp.get_running_app().done_words.append(item.text)


def click_on_done_item(item):
    print(item.text)


def click_on_error_item(item):
    print(item.text)


def import_from(path, source="kindle"):
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
        callback=print,
        item_function=item_function,
        buttons=[ok_button],
    )
