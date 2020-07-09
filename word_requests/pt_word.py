import os
import pickle
import re
from functools import partial

import attr
import pandas as pd
import requests
from googletrans import Translator
from unidecode import unidecode

from google_images_download import google_images_download
from word_requests.urls_and_parsers import (
    dicio_url,
    linguee_api_url,
    parse_dicio_resp,
    parse_linguee_api_resp,
    parse_reverso_resp,
    reverso_url,
)

FROM_LANG = "pt"
TO_LANG = "de"
LANGUAGE = {"pt": "Portuguese", "de": "German", "en": "English", "es": "Spanish"}

PARSE_FUNCTIONS = {
    "linguee": lambda resp: parse_linguee_api_resp(resp.json(), from_lang=FROM_LANG),
    "reverso": lambda resp: parse_reverso_resp(resp.content),
    "dicio": lambda resp: parse_dicio_resp(resp.content),
}

URL_FUNCTIONS = {
    "linguee": partial(linguee_api_url, from_lang=FROM_LANG, to_lang=TO_LANG),
    "reverso": partial(reverso_url, from_lang=FROM_LANG, to_lang=TO_LANG),
    "dicio": dicio_url,
}

translator = Translator()


def translate(string):
    return translator.translate(string, dest=TO_LANG, src=FROM_LANG).text


def html_list(str_list):
    """
    Returns a string, that is displayed as a list in HTML.
    :param str_list:
    :return:
    """
    start = "<ul>\n"
    end = "</ul>\n"
    middle = ['<li type="square">' + item + "</li>\n" for item in str_list]
    return start + "".join(middle) + end


@attr.s
class Word:
    # query properties
    search_term = attr.ib(default="casa")
    data_dir = attr.ib(default="data")
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
    _audio_url = attr.ib(default="")
    add_info_dict = attr.ib(default={})
    conj_table_df = attr.ib(default=pd.DataFrame())

    @property
    def audio_url(self):
        return self._audio_url

    @audio_url.setter
    def audio_url(self, value):
        self._audio_url = value
        if not value:
            return
        print(f"start downloading audio from {value}...")
        r = requests.get(value, allow_redirects=True)
        os.makedirs(f"data/{self.folder()}", exist_ok=True)
        with open(f"data/{self.folder()}/{self.folder()}.mp3", "wb") as file:
            file.write(r.content)
        print("audio download complete.")

    def search_term_utf8(self):
        return unidecode(self.search_term).lower()

    def folder(self):
        return self.search_term_utf8().replace(" ", "_")

    def request_data(self):
        self.__init__(search_term=self.search_term.strip().lower())
        for site in ["linguee", "dicio", "reverso"]:
            url = URL_FUNCTIONS[site](self.search_term)
            resp = requests.get(url)
            parsed_resp = PARSE_FUNCTIONS[site](resp)
            self.update_from_dict(parsed_resp)

    def update_from_dict(self, attr_dict):
        for key, value in attr_dict.items():
            old_val = getattr(self, key)
            if type(old_val) is list:
                value = old_val + value
            setattr(self, key, value)

    def add_translations(self):
        for key in ["examples", "synonyms", "antonyms"]:
            values = getattr(self, key)
            for i, val in enumerate(values):
                if type(val) is str:
                    values[i] = [val, translate(val)]
                elif type(val) is list and len(val) == 1:
                    values[i] = [val[0], translate(val[0])]
            setattr(self, key, values)

    def request_img_urls(self, keywords=None):
        """
        sets self.img_urls from first 20 results of google_images
        """
        keywords = self.search_term_utf8() if keywords is None else keywords
        # keywords = unidecode(keywords).lower()
        response = google_images_download.googleimagesdownload()
        arguments = {
            "keywords": keywords,
            "output_directory": f"data/{self.folder()}",
            "no_directory": True,
            "limit": 10,
            "format": "jpg",
            "language": LANGUAGE[FROM_LANG],
            "no_download": True,
            "print_urls": False,
            "prefix": "img_",
        }
        paths = response.download(arguments)[0][keywords]
        self.image_urls = paths
        return paths

    def html_from_conj_df(self):
        return "\n".join(
            [
                self.conj_table_df.to_html(
                    columns=[col],
                    classes="subj" if "Subjuntivo" in col else "ind",
                    index=False,
                )
                .replace("do Subjuntivo", "")
                .replace("do Indicativo", "")
                for col in self.conj_table_df
            ]
        )

    def mark_examples(self):
        """
        Highlights the search_word in the example sentences using css.
        """
        for word in self.search_term.split(" "):
            self.examples = [
                re.sub(r"((?i)%s)" % word, r"<font color=red><b>\1</font></b>", ex)
                for ex in self.examples
            ]

    @classmethod
    def from_pickle(cls, path):
        with open(path, "rb") as file:
            return cls(pickle.load(file))

    def pickle(self):
        if not os.path.exists(f"data/{self.folder()}"):
            os.makedirs(f"data/{self.folder()}")
        with open(f"data/{self.folder()}/{self.folder()}.p", "wb") as file:
            pickle.dump(attr.asdict(self), file)

    def search(self, new_search_term):
        self.search_term = new_search_term
        path = f"{self.data_dir}/{self.folder()}/{self.folder()}.p"
        if os.path.exists(path):
            try:
                with open(path, "rb") as file:
                    attribute_dict = pickle.load(file)
                    attribute_dict["audio_url"] = attribute_dict.pop("_audio_url")
                    self.__init__(**attribute_dict)
                print(vars(self))
                return True
            except (TypeError, AttributeError):
                print("Could not load previously saved file. Fetching data again...")
        self.request_data()
        self.request_img_urls()
        self.add_translations()
        self.pickle()
        return True


if __name__ == "__main__":
    q = Word(search_term="mesa")
    print(q)
    q.search("casa")
    print(q)
