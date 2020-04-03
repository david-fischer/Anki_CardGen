from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp

class WordProperties(BoxLayout):
    pass

Builder.load_file("anki_scripts/user_input.kv")

class MyApp(MDApp):
    def build(self):
        return Builder.load_string("""
WordProperties:
        """)

if __name__ == "__main__":
    MyApp().run()