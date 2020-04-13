import os
import pickle

from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp

from anki_scripts.dictionary_queries import NoMatchError
from my_kivy.mycard import MyCard
from my_kivy.mychip import MyChip

Builder.load_file("my_kivy/user_input.kv")


class WordProperties(BoxLayout):
    search_term = StringProperty("")
    gender = StringProperty("")
    translations = ListProperty([])
    synonyms = ListProperty([])
    examples = ListProperty([])
    display_limit = 5

    def refresh_data(self):
        word = MDApp.get_running_app().word
        self.ids.translation_chips.clear_widgets()
        self.ids.synonym_chips.clear_widgets()
        self.ids.antonym_chips.clear_widgets()
        self.ids.example_cards.clear_widgets()
        self.ids.explanation_cards.clear_widgets()
        for trans in word.translations[:self.display_limit]:
            self.ids.translation_chips.add_widget(MyChip(label=trans, icon='', check=True))
        for syn in word.synonyms[:self.display_limit]:
            self.ids.synonym_chips.add_widget(MyChip(label=syn, icon='', check=True))
        for ant in word.antonyms[:self.display_limit]:
            self.ids.antonym_chips.add_widget(MyChip(label=ant, icon='', check=True))
        for explanation in word.explanations[:self.display_limit]:
            self.ids.explanation_cards.add_widget(MyCard(text=explanation))
        for ex in word.examples[:self.display_limit]:
            self.ids.example_cards.add_widget(MyCard(text=ex[0] + "\n" + ex[1]))

    def search(self):
        MDApp.get_running_app().word.search_term = self.search_term
        try:
            MDApp.get_running_app().word.get_data()
        except NoMatchError:
            print("No word or phrase found. Maybe some apostrophs are missing or some connection issue?")

    def load_or_search(self):
        MDApp.get_running_app().search_term = self.search_term
        if os.path.exists(f"pickles/{MDApp.get_running_app().word.folder()}.p"):
            self.unpickle()
        else:
            self.search()
            self.pickle()

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


class MyApp(MDApp):
    def build(self):
        return Builder.load_string("""
WordProperties:
        """)


if __name__ == "__main__":
    MyApp().run()
