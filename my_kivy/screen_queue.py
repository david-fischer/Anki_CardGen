from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton

from utils import clean_up, word_list_from_kindle

options_dict = {
    "script-text-outline": "Import from Kindle",
    "note-text":           "Import from Text File"
}


def import_from(button):
    button.parent.close_stack()
    text = options_dict[button.icon]
    if text == "Import from Kindle":
        print("Importing from kindle-html-file...")
        MDApp.get_running_app().open_file_manager(
            ext=[".html"],
            path="./test/test_data/",
            select_path=import_from_kindle
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
    MDApp.get_running_app().file_manager.close()
    words = clean_up(word_list_from_kindle(path), lemmatize=False)
    lemmas = clean_up(words)
    suggested_replacements = [f"{old} -> {new}" for old, new in zip(words, lemmas) if old != new]
    unchanged_words = [word for word, lemma in zip(words, lemmas) if word == lemma]
    MDApp.get_running_app().queue_words = MDApp.get_running_app().queue_words + unchanged_words
    # event = Clock.schedule_once(partial(self.batch_request_words, words=unchanged_words, error_words=error_words))
    event = Clock.schedule_once(lambda dt: choose_replacements_dialog(
        replacements=suggested_replacements))


# def batch_request_words(words, error_words, *args):
#     for word in words:
#         try:
#             MDApp.get_running_app().word.search(word)
#             MDApp.get_running_app().words_dict["queue"].append(word)
#         except (NoMatchError, KeyError):
#             error_words.append(word)
#     print(error_words)
#     MDApp.get_running_app().error_words.append(word)


def choose_replacements_dialog(replacements):
    def item_function(obj):
        MDApp.get_running_app().queue_words.append(obj.text.split(" ")[-1])
        obj.parent.remove_widget(obj)

    def button_function(obj):
        for item in MDApp.get_running_app().dialog.items:
            MDApp.get_running_app().queue_words.append(item.text.split(" ")[0])
            obj.parent.remove_widget(item)
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
