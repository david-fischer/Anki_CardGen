from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.chip import MDChip, MDChooseChip


class MyChip(MDChip):
    def is_checked(self,*args):
        return self.color == self.selected_chip_color

class MyChooseChip(MDChooseChip):
    def choice(self):
        return [chip.label for chip in self.children if chip.is_checked()]

class WordProperties(BoxLayout):
    search_term = StringProperty("casa")
    gender = StringProperty("f")
    translation = StringProperty("Haus")
    synonyms = ListProperty(["domicilio","habitacion"])
    examples = ListProperty(["Estoy em casa.","A casa e grande."])

    def print_all(self):
        print(f""""
Search Term: {self.search_term}
Gender: {self.gender}
Translation: {self.translation}
Synonyms: {self.synonyms}
Examples: {self.examples}
""")

Builder.load_file("user_input.kv")

class MyApp(MDApp):
    def build(self):
        return Builder.load_string("""
WordProperties:
        """)

if __name__ == "__main__":
    MyApp().run()