from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp

from utils import widget_by_id
from word_requests.parser import linguee_did_you_mean, NoMatchError


class WordProperties(BoxLayout):

    def __init__(self, **kwargs):
        super(WordProperties, self).__init__(**kwargs)

    def refresh_data(self):
        word = MDApp.get_running_app().word
        self.ids.translation_chips.element_dicts = [{"text": string} for string in word.translations]
        self.ids.antonym_chips.element_dicts = [{
            "text_orig":  ant[0],
            "text_trans": ant[1]
        }
            for ant in word.antonyms]
        self.ids.synonym_chips.element_dicts = [{
            "text_orig":  syn[0],
            "text_trans": syn[1]
        }
            for syn in word.synonyms]
        self.ids.example_cards.element_dicts = [{
            "text_orig":  ex[0],
            "text_trans": ex[1]
        }
            for ex in word.examples]
        self.ids.explanation_cards.element_dicts = [{"text": string} for string in word.explanations]

    def accept_suggestion(self, suggestion):
        self.load_or_search(suggestion)
        self.refresh_data()

    def load_or_search(self, search_term):
        try:
            MDApp.get_running_app().word.search(search_term)
        except NoMatchError as e:
            suggestions = linguee_did_you_mean(search_term)
            message = f"{search_term} not found on {e.site}." + (" Did you mean... ?" if suggestions else "")
            MDApp.get_running_app().show_dialog(message, suggestions, self.accept_suggestion)
        widget_by_id(
            "/screen_single_word/image_tab/img_search_field").text = search_term
        widget_by_id("/screen_single_word/image_tab/image_grid").get_images()


if __name__ == "__main__":
    class MyApp(MDApp):
        def build(self):
            return Builder.load_string("WordProperties:")


    MyApp().run()
