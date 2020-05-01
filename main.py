import os

import certifi
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.banner import MDBanner
from kivymd.uix.tab import MDTabsBase

from anki_scripts.new_main import Query

os.environ['SSL_CERT_FILE'] = certifi.where()


class Tab(FloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    id = StringProperty("")
    text = StringProperty("")
    icon = StringProperty("")


class SuggestionBanner(MDBanner):

    def on_text(self, asker, question):
        self.show()


class TestApp(MDApp):
    word = ObjectProperty()
    search_term = StringProperty()

    def build(self):
        self.word = Query(search_term=self.search_term)
        self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
        self.theme_cls.theme_style = "Dark"  # "Purple", "Red"
        return Builder.load_file("my_kivy/tabs.kv")

    def on_search_term(self, *args):
        try:
            self.word.search_term = self.search_term
        except AttributeError:
            print("Query not yet initialized.")


if __name__ == "__main__":
    TestApp(search_term="casa").run()
