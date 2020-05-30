import os
import pickle

from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp

from utils import widget_by_id
from word_requests.dictionary_queries import linguee_did_you_mean, NoMatchError


class WordProperties(BoxLayout):
    search_term = StringProperty("")
    gender = StringProperty("")
    translations = ListProperty([])
    synonyms = ListProperty([])
    examples = ListProperty([])
    display_limit = 5

    def __init__(self, **kwargs):
        super(WordProperties, self).__init__(**kwargs)

    def refresh_data(self):
        word = MDApp.get_running_app().word
        self.ids.translation_chips.element_dicts = [{"text": string} for string in word.translations]
        self.ids.antonym_chips.element_dicts = [{
            "text":       ant[1],
            "text_orig":  ant[0],
            "text_trans": ant[1]
        }
            for ant in word.antonyms]
        self.ids.synonym_chips.element_dicts = [{
            "text":       syn[1],
            "text_orig":  syn[0],
            "text_trans": syn[1]
        }
            for syn in word.synonyms]

        self.ids.example_cards.element_dicts = [{
            "text":       ex[1],
            "text_orig":  ex[0],
            "text_trans": ex[1]
        }
            for ex in word.examples]
        self.ids.explanation_cards.element_dicts = [{"text": string} for string in word.explanations]

    def search(self):
        MDApp.get_running_app().word.search_term = self.search_term
        try:
            MDApp.get_running_app().word.get_data()
            return True
        except NoMatchError as e:
            suggestions = linguee_did_you_mean(self.search_term)
            message = f"{self.search_term} not found on {e.site}." +  ( " Did you mean... ?" if suggestions else "")
            MDApp.get_running_app().show_dialog(message, suggestions, self.accept_suggestion)

    def accept_suggestion(self, suggestion):
        self.search_term = suggestion
        self.load_or_search()
        self.refresh_data()

    def load_or_search(self):
        MDApp.get_running_app().word.search_term = self.search_term
        if os.path.exists(f"pickles/{MDApp.get_running_app().word.folder()}.p"):
            self.unpickle()
        else:
            if self.search():
                self.pickle()
        widget_by_id(
            "/screen_single_word/image_tab/img_search_field").text = self.search_term
        widget_by_id("/screen_single_word/image_tab/image_grid").get_images()

    def print_all(self):
        print(f""""
Search Term: {self.search_term}
Gender: {self.gender}
Translation: {self.translation}
Synonyms: {self.synonyms}
Examples: {self.examples}
""")

    def unpickle(self):
        with open(f"pickles/{MDApp.get_running_app().word.folder()}.p", "rb") as file:
            MDApp.get_running_app().word = pickle.load(file)
        self.refresh_data()

    @staticmethod
    def pickle():
        if not os.path.exists("./pickles"):
            os.makedirs("./pickles")
        word = MDApp.get_running_app().word
        with open(f"pickles/{word.folder()}.p", "wb") as file:
            pickle.dump(word, file)


if __name__ == "__main__":
    class MyApp(MDApp):
        def build(self):
            return Builder.load_string("WordProperties:")


    MyApp().run()
