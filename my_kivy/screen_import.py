from functools import partial

from kivy.clock import Clock
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.filemanager import MDFileManager

from utils import clean_up, word_list_from_kindle
from word_requests.urls_and_parsers import NoMatchError


class EditKindleImport(StackLayout):
    file_manager = ObjectProperty()
    manager_open = BooleanProperty(False)
    word_list = ListProperty()

    def __init__(self, **kwargs):
        super(EditKindleImport, self).__init__(**kwargs)
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.load_kindle,
        )
        self.file_manager.ext = [".html"]

    def load_kindle(self, path):
        self.exit_manager()
        words = clean_up(word_list_from_kindle(path), lemmatize=False)
        lemmas = clean_up(words)
        suggested_replacements = [f"{old} -> {new}" for old, new in zip(words, lemmas) if old != new]
        unchanged_words = [word for word, lemma in zip(words, lemmas) if word == lemma]
        error_words = []
        event = Clock.schedule_once(partial(self.batch_request_words, words=unchanged_words, error_words=error_words))
        event2 = Clock.schedule_once(partial(self.choose_replacements, replacements=suggested_replacements,
                                             error_words=error_words))

    def batch_request_words(self, dt, words, error_words, *args):
        for word in words:
            try:
                MDApp.get_running_app().word.search(word)
            except (NoMatchError, KeyError):
                error_words.append(word)
        print(error_words)

    def choose_replacements(self, dt, replacements, error_words):
        words = []

        def item_function(obj):
            words.append(obj.text.split(" ")[-1])
            obj.parent.remove_widget(obj)

        def button_function(obj):
            for item in MDApp.get_running_app().dialog.items:
                words.append(item.text.split(" ")[0])
                obj.parent.remove_widget(item)
            MDApp.get_running_app().dialog.dismiss()
            Clock.schedule_once(partial(self.batch_request_words, words=words, error_words=error_words))

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

    def file_manager_open(self):
        self.file_manager.show('./test/test_data/')  # output manager to the screen
        self.manager_open = True

    def exit_manager(self, *args):
        self.manager_open = False
        self.file_manager.close()
