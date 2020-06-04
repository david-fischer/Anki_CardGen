from functools import partial

from kivy.clock import Clock
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
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
        words = clean_up(word_list_from_kindle(path),lemmatize=False)
        lemmas = clean_up(words)
        suggested_replacements = [f"{old} -> {new}" for old, new in zip(words, lemmas) if old != new]
        unchanged_words = [word for word,lemma in zip(words,lemmas) if word==lemma]
        error_words = []
        event = Clock.schedule_once(partial(self.batch_request_words, words=unchanged_words, error_words=error_words))
        event2 = Clock.schedule_once(partial(self.choose_replacements, replacements=suggested_replacements))

    def batch_request_words(self,dt,words,error_words,*args):
        for word in words:
            try:
                MDApp.get_running_app().word.search(word)
            except NoMatchError:
                error_words.append(word)
        print(error_words)

    # def choose_replacements(self,dt,replacements,*args):
    #     words = []
    #     def button_function(obj):
    #         words.append(obj.text.split(" ")[-1])
    #     MDApp.get_running_app().show_dialog(
    #         message="Some words are not in their dictionary form. The following replacements are suggested:",
    #         options=replacements,
    #         callback=print,
    #         button_function=lambda x: x.parent.remove_widget(x)
    #     )


    def file_manager_open(self):
        self.file_manager.show('./test/test_data/')  # output manager to the screen
        self.manager_open = True

    def exit_manager(self, *args):
        self.manager_open = False
        self.file_manager.close()
