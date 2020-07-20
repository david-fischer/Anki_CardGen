"""
Contains the necessary functions and classes for the screen screen_single_word.
"""
import os

import certifi
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase

from parsers import linguee_did_you_mean, NoMatchError
from utils import (
    compress_img,
    set_screen,
    tag_word_in_sentence,
)

os.environ["SSL_CERT_FILE"] = certifi.where()


class WordProperties(BoxLayout):
    """
    Consists of the UI-elements that display the data obtained by :class:`words.Word` and lets the user choose which
    data to include on the card.
    """

    def refresh_data(self):
        """Refresh UI with the data from :class:`words.Word`."""
        word = MDApp.get_running_app().word
        self.ids.translations.child_dicts = [
            {"text": string} for string in word.translations
        ]
        self.ids.images.child_dicts = [{"source": string} for string in word.image_urls]
        for attribute in ["antonyms", "synonyms", "examples", "explanations"]:
            self.ids[attribute].child_dicts = [
                {"text_orig": x[0], "text_trans": x[1]}
                for x in getattr(word, attribute)
            ]

    def accept_suggestion(self, suggestion):
        """Use Suggestion for new search."""
        self.ids.search_field.text = suggestion
        self.load_or_search(suggestion)

    def load_or_search(self, search_term):
        """Searches for word, suggests alternative if not found and shows images."""
        try:
            MDApp.get_running_app().word.search(search_term)
            self.refresh_data()
            self.parent.scroll_y = 1
        except NoMatchError as error:
            suggestions = linguee_did_you_mean(search_term)
            MDApp.get_running_app().show_dialog(
                message=f"{search_term} not found on {error.site}."
                + (" Did you mean... ?" if suggestions else ""),
                options=suggestions,
                item_callback=lambda obj: self.accept_suggestion(obj.text),
                close_on_item=True,
            )

    def get_user_selection_dict(self):
        """
        Returns current user selection in the form needed by add_anki_card.

        Example and explanation strings are tagged using :func:`utils.tag_word_in_sentence`.
        """
        selections = [
            {"key": "Translation", "id": "translations", "attr": "text"},
            {"key": "Synonym", "id": "synonyms", "attr": "text_orig"},
            {"key": "Antonym", "id": "antonyms", "attr": "text_orig"},
            {"key": "Explanation", "id": "explanations", "attr": "text_orig"},
            {"key": "Example", "id": "examples", "attr": "text_orig"},
            {"key": "ExampleTranslation", "id": "examples", "attr": "text_trans"},
        ]
        result_dict = {
            d["key"]: ",".join(self.ids[d["id"]].get_checked(property_name=d["attr"]))
            for d in selections
        }
        for key in ["Example", "Explanation"]:
            result_dict[key] = tag_word_in_sentence(
                result_dict[key], MDApp.get_running_app().word.search_term
            )
        return result_dict

    def download_selected_image(self):
        """Downloads the currently selected image to :meth:`words.Word.base_path` + ".jpg" """
        # TODO: show spinner and cancel after certain time
        # TODO: Correct behavior on Error
        out_path = MDApp.get_running_app().word.base_path() + ".jpg"
        img_url = self.ids.images.get_checked(property_name="source")[0]
        r_i = UrlRequest(
            img_url,
            file_path=out_path,
            on_success=lambda *args: compress_img(out_path),
        )
        r_i.wait()

    def complete_generation(self):
        """
        Generate Anki card from current user selection and changes screen.

        If the word was in the queue, returns to screen_queue.
        Else, resets the screen_single_word and changes to the edit_tab.
        """
        self.download_selected_image()
        word = MDApp.get_running_app().word
        result_dict = {
            **word.get_fix_card_dict(),
            **self.get_user_selection_dict(),
        }
        MDApp.get_running_app().add_anki_card(result_dict)
        self.ids.search_field.text = ""
        word.__init__()
        self.refresh_data()
        # TODO: Why does the focussing not work anymore?
        self.ids.search_field.focus = True
        self.parent.scroll_y = 1
        search_term = result_dict["Word"]
        if search_term in MDApp.get_running_app().queue_words:
            set_screen("screen_queue")
            MDApp.get_running_app().queue_words.remove(search_term)


# class ImageSearchResultGrid(MyCheckImageGrid):
#     """Extends the :class:`mychooser.MyCheckImageGrid` by the :meth:`get_images` method."""
#
#     def on_child_dicts(self, *_):
#         if len(self.children) == len(self.child_dicts):
#             for image, child_dict in zip(self.children, self.child_dicts):
#                 image.source = child_dict["source"]
#                 # image._img_widget.container.image.bind(on_error=f)
#         else:
#             super(ImageSearchResultGrid, self).on_child_dicts(*_)
#
#     def get_images(self, keywords=None):
#         """
#         Sets images displayed in :class:`ImageSearchResultGrid`.
#
#         Args:
#             keywords:
#                 If None, uses :attr:`words.Word.img_urls`, else uses result of :meth:`words.Word.request_img_urls`
#                 for given keywords. (Default = None)
#         """
#         word = MDApp.get_running_app().word
#         paths = (
#             word.image_urls
#             if keywords is None
#             else word.request_img_urls(keywords=keywords)
#         )
#         self.child_dicts = [{"source": url} for url in paths]


# TODO: Move
class Tab(FloatLayout, MDTabsBase):
    """Class implementing content for a tab. """

    id = StringProperty("")
    """:class:`~kivy.properties.StringProperty`"""

    text = StringProperty("")
    """:class:`~kivy.properties.StringProperty`"""

    icon = StringProperty("")
    """:class:`~kivy.properties.StringProperty`"""


# pylint: disable = W,C,R,I
if __name__ == "__main__":

    class TestApp(MDApp):
        def build(self):
            return Builder.load_file("screen_single_word.kv")

    TestApp().run()
