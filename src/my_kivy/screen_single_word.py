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

from my_kivy.mychooser import MyCheckImageGrid
from parsers import linguee_did_you_mean, NoMatchError
from utils import (
    compress_img,
    selection_helper,
    set_screen,
    tag_word_in_sentence,
    widget_by_id,
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
        self.ids.translation_chips.child_dicts = [
            {"text": string} for string in word.translations
        ]
        self.ids.antonym_chips.child_dicts = [
            {"text_orig": ant[0], "text_trans": ant[1]} for ant in word.antonyms
        ]
        self.ids.synonym_chips.child_dicts = [
            {"text_orig": syn[0], "text_trans": syn[1]} for syn in word.synonyms
        ]
        self.ids.example_cards.child_dicts = [
            {"text_orig": ex[0], "text_trans": ex[1]} for ex in word.examples
        ]
        self.ids.explanation_cards.child_dicts = [
            {"text_orig": expl[0], "text_trans": expl[1]} for expl in word.explanations
        ]
        self.ids.images.child_dicts = [{"source": string} for string in word.image_urls]

    def accept_suggestion(self, suggestion):
        """Use Suggestion for new search."""
        self.ids.search_field.text = suggestion
        self.load_or_search(suggestion)

    def load_or_search(self, search_term):
        """Searches for word, suggests alternative if not found and shows images."""
        try:
            MDApp.get_running_app().word.search(search_term)
            # widget_by_id("/screen_single_word/image_tab/image_grid").get_images()
            # widget_by_id(
            #     "/screen_single_word/image_tab/img_search_field"
            # ).text = search_term
            self.refresh_data()
        except NoMatchError as error:
            suggestions = linguee_did_you_mean(search_term)
            MDApp.get_running_app().show_dialog(
                message=f"{search_term} not found on {error.site}."
                + (" Did you mean... ?" if suggestions else ""),
                options=suggestions,
                callback=self.accept_suggestion,
            )


class ImageSearchResultGrid(MyCheckImageGrid):
    """Extends the :class:`mychooser.MyCheckImageGrid` by the :meth:`get_images` method."""

    def on_child_dicts(self, *_):
        if len(self.children) == len(self.child_dicts):
            for image, child_dict in zip(self.children, self.child_dicts):
                image.source = child_dict["source"]
                # image._img_widget.container.image.bind(on_error=f)
        else:
            super(ImageSearchResultGrid, self).on_child_dicts(*_)

    def get_images(self, keywords=None):
        """
        Sets images displayed in :class:`ImageSearchResultGrid`.

        Args:
            keywords:
                If None, uses :attr:`words.Word.img_urls`, else uses result of :meth:`words.Word.request_img_urls`
                for given keywords. (Default = None)
        """
        word = MDApp.get_running_app().word
        paths = (
            word.image_urls
            if keywords is None
            else word.request_img_urls(keywords=keywords)
        )
        self.child_dicts = [{"source": url} for url in paths]


def download_selected_image():
    """Downloads the currently selected image to :meth:`words.Word.base_path`+".jpg" """
    # TODO: show spinner and cancel after certain time
    # TODO: Correct behavior on Error
    out_path = MDApp.get_running_app().word.base_path() + ".jpg"
    try:
        img_url = widget_by_id("/screen_single_word/image_tab/image_grid/").get_checked(
            property_name="source"
        )[0]
        print(img_url)
        r_i = UrlRequest(
            img_url,
            file_path=out_path,
            on_success=lambda *args: compress_img(out_path),
        )
        r_i.wait()
    except IndexError:
        # TODO: change to a popup
        print("Error with image download. Try different Image instead.")


def get_selection_dict():
    """Obtains Dictionary with all fields necessary for the Anki card from the current user selection."""
    word = MDApp.get_running_app().word
    word_prop = widget_by_id("/screen_single_word/edit_tab/word_prop")
    base_path = word.base_path()
    selections = {
        "translation_chips": ["text"],
        "synonym_chips": ["text_orig", "text_trans"],
        "antonym_chips": ["text_orig", "text_trans"],
        "explanation_cards": ["text"],
        "example_cards": ["text_orig", "text_trans"],
    }
    out = {}
    for key, props in selections.items():
        new_key = key.split("_")[0]
        out[new_key] = selection_helper(word_prop, id_str=key, props=props)
    # print(out)
    # TODO: Deal with the case that either audio or image is not downloaded
    return {
        "Word": word.search_term,
        "Translation": ", ".join(out["translation"]),
        "Synonym": out["synonym"][0] if out["synonym"] else "",
        "Image": f'<img src="{word.folder()}.jpg">',
        "Explanation": tag_word_in_sentence(out["explanation"][0], word.search_term)
        if out["explanation"]
        else "",
        "ExampleTranslation": out["example"][1] if out["example"] else "",
        "Example": tag_word_in_sentence(out["example"][0], word.search_term)
        if out["example"]
        else "",
        "ConjugationTable": word.conj_table_html,
        "Audio": f"[sound:{word.search_term}.mp3]",
        "Antonym": out["antonym"][0] if out["antonym"] else "",
        "AdditionalInfo": str(word.add_info_dict),
        "media_files": [f"{base_path}.{ext}" for ext in ["jpg", "mp3"]],
    }


class Tab(FloatLayout, MDTabsBase):
    """Class implementing content for a tab. """

    id = StringProperty("")
    """:class:`~kivy.properties.StringProperty`"""

    text = StringProperty("")
    """:class:`~kivy.properties.StringProperty`"""

    icon = StringProperty("")
    """:class:`~kivy.properties.StringProperty`"""


def complete_generation():
    """
    Generate Anki card from current user selection and changes screen.

    If the word was in the queue, returns to screen_queue.
    Else, resets the screen_single_word and changes to the edit_tab.
    """
    download_selected_image()
    result_dict = get_selection_dict()
    MDApp.get_running_app().add_anki_card(result_dict)
    widget_by_id("/screen_single_word/tabs/carousel").index = 0
    widget_by_id("/screen_single_word/edit_tab/word_prop/search_field").text = ""
    widget_by_id("/screen_single_word/edit_tab/word_prop/search_field").focus = True
    MDApp.get_running_app().word.__init__()
    widget_by_id("/screen_single_word/edit_tab/word_prop").refresh_data()
    search_term = result_dict["Word"]
    if search_term in MDApp.get_running_app().queue_words:
        set_screen("screen_queue")
        MDApp.get_running_app().queue_words.remove(search_term)


# pylint: disable = W,C,R,I
if __name__ == "__main__":

    class TestApp(MDApp):
        def build(self):
            return Builder.load_file("screen_single_word.kv")

    TestApp().run()
    TestApp().run()
