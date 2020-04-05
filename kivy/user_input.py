from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.chip import MDChip, MDChooseChip

from mychip import MyChip,MyChooseChip

Builder.load_file("user_input.kv")


class WordProperties(BoxLayout):
    search_term = StringProperty("casa")
    gender = StringProperty("f")
    translation = StringProperty("Haus")
    synonyms = ListProperty(["domicilio", "habitacion"])
    examples = ListProperty(["Estoy em casa.", "A casa e grande."])

    def refresh_data(self):
        Query = MDApp.get_running_app().Query
        self.synonyms = Query.synonyms
        self.examples = Query.examples
        self.translation = Query.translated
        self.gender = Query.gender

    def post_init(self,):
        self.ids.synonym_chips.clear_widgets()
        self.ids.example_chips.clear_widgets()
        for syn in self.synonyms:
            self.ids.synonym_chips.add_widget(MyChip(label=syn,icon='',check=True))
        for ex in self.examples:
            self.ids.example_chips.add_widget(MyChip(label=ex,icon='',check=True))


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
