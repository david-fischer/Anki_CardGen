import os

import certifi
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.banner import MDBanner
from kivymd.uix.tab import MDTabsBase

from anki_scripts.new_main import Query
from my_kivy.mychooser import MyCheckImageGrid

os.environ['SSL_CERT_FILE'] = certifi.where()


def widget_by_id(string):
    """
    :arg string: "/edit_tab/word_prop/translation_chips
    :returns widget root.ids.edit_tab.ids.word_prop ... usw
    """
    ids = string.split("/")
    ids = [id for id in ids if id != ""]
    obj = MDApp.get_running_app().root
    for id in ids:
        obj = getattr(obj.ids, id)
    return obj


def selection_helper(base, id=None, props="text"):
    base_obj = getattr(base.ids, id) if id is not None else base
    objects = base_obj.get_checked()
    return [[getattr(obj, property) for property in props] for obj in objects]


def make_card():
    word = MDApp.get_running_app().word
    word_prop = widget_by_id("/edit_tab/word_prop")
    img_url = widget_by_id("/image_tab/image_grid/").get_checked(property="source")
    audio_url = word.audio_url
    UrlRequest(img_url, file_path=f"data/{word.folder()}/image.jgp", on_success=lambda *args: print("DONE IMG!"))
    UrlRequest(audio_url, file_path=f"data/{word.folder()}/audio.mp3", on_success=lambda *args: print("DONE AUDIO!"))
    selections = {
        "translation_chips": ["text"],
        "synonym_chips": ["text_orig", "text_trans"],
        "antonym_chips": ["text_orig", "text_trans"],
        "explanation_cards": ["text"],
        "example_cards": ["text_orig", "text_trans"],
    }
    for key, props in selections.items():
        print(key, props)
        selections[key] = selection_helper(word_prop, id=key, props=props)


class Tab(FloatLayout, MDTabsBase):
    """Class implementing content for a tab. """
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
