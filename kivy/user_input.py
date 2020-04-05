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

    def post_init(self,):
        for syn in self.synonyms:
            print(self)
            self.ids.synonym_chips.add_widget(MyChip(label=syn,icon='',check=True))

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
