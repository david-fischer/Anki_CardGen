import os

import certifi
from kivy.properties import StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.banner import MDBanner
from kivymd.uix.tab import MDTabsBase

from my_kivy.mychooser import MyCheckImageGrid
from utils import selection_helper, widget_by_id

os.environ['SSL_CERT_FILE'] = certifi.where()


def make_card():
    word = MDApp.get_running_app().word
    word_prop = widget_by_id("/screen_single_word/edit_tab/word_prop")
    try:
        img_url = widget_by_id("/screen_single_word/image_tab/image_grid/").get_checked(property="source")[
            0].replace("http:", "https:")
        print(img_url)
        # UrlRequest(img_url, file_path=f"data/{word.folder()}/{word.folder()}.jpg",
        #           debug=True, timeout=5,
        #           on_success=lambda *args: print("Finished downloading image."))
    except IndexError:
        # TODO: change to a popup
        print("Error with image download. Try different Image instead.")
    #audio_url = word.audio_url
    # UrlRequest(audio_url, file_path=f"data/{word.folder()}/{word.folder()}.mp3",
    #           on_success=lambda *args: print("Finished downloading audio."))
    selections = {
        "translation_chips": ["text"],
        "synonym_chips":     ["text_orig", "text_trans"],
        "antonym_chips":     ["text_orig", "text_trans"],
        "explanation_cards": ["text"],
        "example_cards":     ["text_orig", "text_trans"],
    }
    out = {}
    for key, props in selections.items():
        new_key = key.split("_")[0]
        out[new_key] = selection_helper(word_prop, id=key, props=props)
    # return {
    #     'Word':               word.search_term,
    #     'Translation':        ", ".join(selections["translation"]),
    #     'Synonym':            selections["synonym"],
    #     'Image':              "",
    #     'Explanation':        "",
    #     'ExampleTranslation': "",
    #     'Example':            "",
    #     'ConjugationTable':   "",
    #     'Audio':              "",
    #     'Antonym':            "",
    #     'AdditionalInfo':     ","
    # }


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
