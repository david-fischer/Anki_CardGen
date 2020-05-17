import os

import certifi
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty, Property
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.banner import MDBanner
from kivymd.uix.tab import MDTabsBase

from anki_scripts.new_main import Query
from my_kivy.mychooser import MyCheckImageGrid

os.environ['SSL_CERT_FILE'] = certifi.where()


def make_card():


class Tab(FloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    id = StringProperty("")
    text = StringProperty("")
    icon = StringProperty("")


class ImageSearchResultGrid(MyCheckImageGrid):
    def get_images(self, keywords=None):
        word = MDApp.get_running_app().word
        paths = word.image_urls if keywords is None else word.request_img_urls(keywords=keywords)
        self.element_dicts = [{"source": url} for url in paths]


class SuggestionBanner(MDBanner):
    message = StringProperty()
    respond_to = Property(None)

    def __init__(self, **kwargs):
        super(SuggestionBanner, self).__init__(**kwargs)
        self.register_event_type("on_ok")

    def on_message(self, asker, question):
        self.text = [self.message]
        self.show()

    def on_ok(self, *args):
        self.hide()

    def hide(self, *args):
        super(SuggestionBanner, self).hide()


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
