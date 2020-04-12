import os
import re

import attr
import pandas as pd
from translate import Translator
from unidecode import unidecode

from anki_scripts.dictionary_queries import request_data_from_linguee, \
    request_data_from_dicio, request_examples_from_reverso
from google_images_download import google_images_download

FROM_LANG = "pt"
TO_LANG = "de"
LANGUAGE = {"pt": "Portuguese", "de": "German", "en": "English", "es": "Spanish"}

translator = Translator(from_lang=FROM_LANG, to_lang=TO_LANG)


def html_list(str_list):
    """
    Returns a string, that is displayed as a list in HTML.
    :param str_list:
    :return:
    """
    start = "<ul>\n"
    end = "</ul>\n"
    middle = ["<li type=\"square\">" + item + "</li>\n" for item in str_list]
    return start + "".join(middle) + end


@attr.s
class Query:
    # query properties
    search_term = attr.ib(default="casa")
    # word properties
    word_type = attr.ib(default="")  # verb noun etc
    gender = attr.ib(default="")
    examples = attr.ib(default=[])
    explanations = attr.ib(default=[])
    synonyms = attr.ib(default=[])
    antonyms = attr.ib(default=[])
    translations = attr.ib(default=[])
    trans_syns = attr.ib(default=[])
    image_urls = attr.ib(default=[])
    audio_url = attr.ib(default="")
    add_info_dict = attr.ib(default={})
    conj_table_df = attr.ib(default=pd.DataFrame())
    # other
    anki_user = attr.ib(default="new_user")
    output_path = attr.ib(default=".")

    def search_term_utf8(self):
        return unidecode(self.search_term)

    def folder(self):
        return self.search_term_utf8().replace(" ", "_")

    def get_data(self):
        self.search_term = self.search_term.strip().lower()
        os.makedirs(f"data/{self.folder()}", exist_ok=True)
        self.request_dict_data()
        try:
            self.request_img_urls()
        except:
            print("could not download images :(")

    def request_dict_data(self):
        """
        Uses ask from dictionary_queries.py to fill the fields:
        self.translations
        self.audio_url
        self.word_type
        self.gender
        self.examples
        self.explanations
        self.synonyms
        self.antonyms
        self.add_info_dict
        """
        self.translations, \
        self.audio_url, \
        self.word_type, \
        self.gender, \
            = request_data_from_linguee(self.search_term, FROM_LANG)
        self.explanations, \
        self.synonyms, \
        self.antonyms, \
        self.examples, \
        self.add_info_dict, \
        self.conj_table_df = request_data_from_dicio(self.search_term)
        self.examples = [[ex, translator.translate(ex)] for ex in self.examples] + request_examples_from_reverso(
            self.search_term)

    def request_img_urls(self):
        """
        sets self.img_urls from first 20 results of google_images
        """
        response = google_images_download.googleimagesdownload()
        arguments = {"keywords": self.search_term_utf8(),
                     "output_directory": f"data/{self.folder()}",
                     "no_directory": True,
                     "limit": 20,
                     "format": "jpg",
                     "language": LANGUAGE[FROM_LANG],
                     "no_download": True,
                     "print_urls": True,
                     "prefix": "img_",
                     "save_source": "source",
                     }
        paths = response.download(arguments)[0][self.search_term_utf8()]
        self.image_urls = paths

    def html_from_conj_df(self):
        return "\n".join([
            self.conj_table_df.to_html(columns=[col],
                                       classes="subj" if "Subjuntivo" in col else "ind",
                                       index=False
                                       ).replace("do Subjuntivo", "").replace("do Indicativo", "")
            for col in self.conj_table_df
        ])

    def mark_examples(self):
        """
        Highlights the search_word in the example sentences using css.
        """
        for word in self.search_term.split(" "):
            self.examples = [re.sub(r'((?i)%s)' % word, r'<font color=red><b>\1</font></b>', ex) for ex in
                             self.examples]


if __name__ == "__main__":
    q = Query(search_term="mesa")
    print(q)
