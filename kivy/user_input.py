from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp

from mychip import MyChip

Builder.load_file("user_input.kv")


class WordProperties(BoxLayout):
    search_term = StringProperty("")
    gender = StringProperty("")
    translation = StringProperty("")
    synonyms = ListProperty([])
    examples = ListProperty([])

    def refresh_data(self):
        word = MDApp.get_running_app().word
        self.synonyms = word.synonyms
        self.examples = word.examples
        self.translation = word.translated
        self.gender = word.gender

    def post_init(self, ):
        self.ids.synonym_chips.clear_widgets()
        self.ids.example_chips.clear_widgets()
        for syn in self.synonyms:
            self.ids.synonym_chips.add_widget(MyChip(label=syn, icon='', check=True))
        for ex in self.examples:
            self.ids.example_chips.add_widget(MyChip(label=ex, icon='', check=True))

    def print_all(self):
        print(f""""
Search Term: {self.search_term}
Gender: {self.gender}
Translation: {self.translation}
Synonyms: {self.synonyms}
Examples: {self.examples}
""")


class MyApp(MDApp):
    def build(self):
        return Builder.load_string("""
WordProperties:
        """)


if __name__ == "__main__":
    MyApp().run()
