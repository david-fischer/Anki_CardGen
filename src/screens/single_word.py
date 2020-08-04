"""Contains the necessary functions and classes for the screen single_word."""
import os

import certifi
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp

from parsers import linguee_did_you_mean, NoMatchError
from utils import (
    compress_img,
    set_screen,
    tag_word_in_sentence,
)

os.environ["SSL_CERT_FILE"] = certifi.where()


class WordProperties(FloatLayout):
    """
    UI for picking content of Anki card.

    Consists of the UI-elements that display the data obtained by :class:`words.Word` and lets the user choose which
    data to include on the card.
    """

    def refresh_data(self):
        """Refresh UI with the data from :class:`words.Word`."""
        print(self.parent.parent.ids)
        word = MDApp.get_running_app().word
        self.ids.translations.data = [{"text": string} for string in word.translations]
        self.ids.images.data = [{"source": string} for string in word.image_urls]
        for attribute in ["antonyms", "synonyms", "examples", "explanations"]:
            self.ids[attribute].data = [
                {"text_orig": x[0], "text_trans": x[1]}
                for x in getattr(word, attribute)
            ]

    def accept_suggestion(self, suggestion):
        """Use Suggestion for new search."""
        self.ids.search_field.text = suggestion
        self.load_or_search(suggestion)

    def load_or_search(self, search_term):
        """Search for word, suggest alternative if not found and show images."""
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
        Return current user selection as dict (in the form needed by :attr:`main.AnkiCardGenApp.add_anki_card`).

        Example and explanation strings are tagged using :func:`utils.tag_word_in_sentence`.
        """
        selections = [
            {"key": "translation", "id": "translations", "attr": "text"},
            {"key": "synonym", "id": "synonyms", "attr": "text_orig"},
            {"key": "antonym", "id": "antonyms", "attr": "text_orig"},
            {"key": "explanation", "id": "explanations", "attr": "text_orig"},
            {"key": "example", "id": "examples", "attr": "text_orig"},
            {"key": "example_translation", "id": "examples", "attr": "text_trans"},
        ]
        result_dict = {
            d["key"]: ",".join(self.ids[d["id"]].get_checked(attribute_name=d["attr"]))
            for d in selections
        }
        for key in ["example", "explanation"]:
            result_dict[key] = tag_word_in_sentence(
                result_dict[key], MDApp.get_running_app().word.search_term
            )
        return result_dict

    def download_selected_image(self):
        """Download the currently selected image to :meth:`words.Word.base_path` + ".jpg"."""
        # TODO: show spinner and cancel after certain time
        # TODO: Correct behavior on Error
        out_path = MDApp.get_running_app().word.base_path() + ".jpg"
        img_url = self.ids.images.get_checked(attribute_name="source")[0]
        r_i = UrlRequest(
            img_url,
            file_path=out_path,
            on_success=lambda *args: compress_img(out_path),
        )
        r_i.wait()

    def complete_generation(self):
        """
        Generate Anki card from current user selection and changes screen.

        If the word was in the queue, returns to queue.
        Else, resets the single_word and changes to the edit_tab.
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
        # TODO: Why does the focussing not work anymore? -> Clock.schedule_once
        self.ids.search_field.focus = True
        self.parent.scroll_y = 1
        search_term = result_dict["word"]
        if search_term in MDApp.get_running_app().word_state_dict:
            set_screen("queue")
            MDApp.get_running_app().word_state_dict[search_term] = "done"


# class ImageSearchResultGrid(MyCheckImageGrid):
#     """Extends the :class:`selection_widgets.MyCheckImageGrid` by the :meth:`get_images` method."""
#
#     def on_data(self, *_):
#         if len(self.children) == len(self.data):
#             for image, child_dict in zip(self.children, self.data):
#                 image.source = child_dict["source"]
#                 # image._img_widget.container.image.bind(on_error=f)
#         else:
#             super(ImageSearchResultGrid, self).on_data(*_)
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
#         self.data = [{"source": url} for url in paths]


# pylint: disable = W,C,R,I
if __name__ == "__main__":

    class _TestApp(MDApp):
        def build(self):
            return Builder.load_file("single_word.kv")

    _TestApp().run()
