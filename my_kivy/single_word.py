import os

import certifi
from kivy.network.urlrequest import UrlRequest
from kivy.properties import StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.tab import MDTabsBase

from my_kivy.mychooser import MyCheckImageGrid
from utils import now_string, save_dict_to_csv, selection_helper, widget_by_id

os.environ['SSL_CERT_FILE'] = certifi.where()


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
        'Image':              f'<img src="{base_path}.jpg">',
        'Explanation':        out["explanation"][0],
        'ExampleTranslation': out["example"][1],
        'Example':            out["example"][0],
        'ConjugationTable':   "",
        'Audio':              f'[sound:{base_path}.mp3]',
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
    MDApp.get_running_app().anki.write_apkg(now_string() + ".apgk")
    widget_by_id("/single_word_screen//")
