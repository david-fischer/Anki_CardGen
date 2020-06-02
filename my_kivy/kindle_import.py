from kivy.properties import BooleanProperty, ListProperty, ObjectProperty
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.stacklayout import StackLayout
from kivymd.uix.filemanager import MDFileManager

from utils import clean_up, widget_by_id, word_list_from_kindle


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
        # data_table = MDDataTable(
        #     size_hint=(0.8,None),
        #     width=200,
        #     column_data=[
        #         ("Originally", dp(30)),
        #         ("Corrected", dp(30)),
        #     ],
        #     check=True,
        #     row_data=zip(["1","2","3","4"],["1","2","3","4"]),
        #     rows_num=len([1,2,3,4]),
        # )
        # print(data_table.row_data)
        # self.add_widget(data_table)
        suggested_replacements = [f"{old} -> {new}" for old, new in zip(words, lemmas) if old != new]
        unchanged_words = [word for word,lemma in zip(words,lemmas) if word==lemma]
        for word in unchanged_words:
            widget_by_id("/screen_single_word/edit_tab/word_prop").search_term = word
            widget_by_id("/screen_single_word/edit_tab/word_prop").load_or_search()

    def file_manager_open(self):
        self.file_manager.show('./test/test_data/')  # output manager to the screen
        self.manager_open = True

    def exit_manager(self, *args):
        self.manager_open = False
        self.file_manager.close()
