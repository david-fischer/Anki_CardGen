import os

import certifi
from kivy.network.urlrequest import UrlRequest
from kivy.properties import StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.toast import toast
from kivymd.uix.tab import MDTabs, MDTabsBase

from my_kivy.mychooser import MyCheckImageGrid
from utils import now_string, save_dict_to_csv, selection_helper

os.environ['SSL_CERT_FILE'] = certifi.where()

from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp

from utils import widget_by_id
from word_requests.urls_and_parsers import linguee_did_you_mean, NoMatchError


class WordProperties(BoxLayout):

    def __init__(self, **kwargs):
        super(WordProperties, self).__init__(**kwargs)

    def refresh_data(self):
        word = MDApp.get_running_app().word
        self.ids.translation_chips.element_dicts = [{"text": string} for string in word.translations]
        self.ids.antonym_chips.element_dicts = [{
            "text_orig":  ant[0],
            "text_trans": ant[1]
        }
            for ant in word.antonyms]
        self.ids.synonym_chips.element_dicts = [{
            "text_orig":  syn[0],
            "text_trans": syn[1]
        }
            for syn in word.synonyms]
        self.ids.example_cards.element_dicts = [{
            "text_orig":  ex[0],
            "text_trans": ex[1]
        }
            for ex in word.examples]
        self.ids.explanation_cards.element_dicts = [{"text": string} for string in word.explanations]

    def accept_suggestion(self, suggestion):
        self.ids.search_field.text = suggestion
        self.load_or_search(suggestion)
        self.refresh_data()

    def load_or_search(self, search_term):
        try:
            MDApp.get_running_app().word.search(search_term)
            widget_by_id("/screen_single_word/image_tab/image_grid").get_images()
            widget_by_id(
                "/screen_single_word/image_tab/img_search_field").text = search_term
        except NoMatchError as e:
            suggestions = linguee_did_you_mean(search_term)
            message = f"{search_term} not found on {e.site}." + (" Did you mean... ?" if suggestions else "")
            MDApp.get_running_app().show_dialog(message, suggestions, self.accept_suggestion)


def get_selection_dict():
    word = MDApp.get_running_app().word
    word_prop = widget_by_id("/screen_single_word/edit_tab/word_prop")
    base_path = f"data/{word.folder()}/{word.folder()}"
    try:
        img_url = widget_by_id("/screen_single_word/image_tab/image_grid/").get_checked(property="source")[
            0].replace("http:", "https:")
        print(img_url)
        r_i = UrlRequest(img_url, file_path=f"{base_path}.jpg",
                         on_success=lambda *args: print("Finished downloading image."))
    except IndexError:
        # TODO: change to a popup
        print("Error with image download. Try different Image instead.")
    audio_url = word.audio_url
    r_a = UrlRequest(audio_url, file_path=f"{base_path}.mp3",
                     on_success=lambda *args: print("Finished downloading audio."))
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
    # print(out)
    # TODO: Deal with the case that either audio or image is not downloaded
    r_i.wait()
    r_a.wait()
    return {
        'Word':               word.search_term,
        'Translation':        ", ".join(out["translation"]),
        'Synonym':            out["synonym"][0] if out["synonym"] else "",
        'Image':              f'<img src="{word.search_term}.jpg">',
        'Explanation':        out["explanation"][0],
        'ExampleTranslation': out["example"][1],
        'Example':            out["example"][0],
        'ConjugationTable':   "",
        'Audio':              f'[sound:{word.search_term}.mp3]',
        'Antonym':            out["antonym"][0] if out["antonym"] else "",
        'AdditionalInfo':     str(word.add_info_dict),
        'media_files':        [f"{base_path}.{ext}" for ext in ["jpg", "mp3"]],
    }


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


def confirm_choice():
    result_dict = get_selection_dict()
    print(result_dict)
    toast(f'Added card for "{result_dict["Word"]}" to Deck.', duration=3)
    save_dict_to_csv(result_dict, "out.csv")
    MDApp.get_running_app().anki.add_card(**result_dict)
    MDApp.get_running_app().anki.write_apkg(now_string() + ".apkg")
    widget_by_id("/screen_single_word/tabs/carousel").index = 0
    widget_by_id("/screen_single_word/edit_tab/word_prop/search_field").text = ""
    widget_by_id("/screen_single_word/edit_tab/word_prop/search_field").focus = True
    MDApp.get_running_app().word.__init__()
    widget_by_id("/screen_single_word/edit_tab/word_prop").refresh_data()


