import os
import re

import attr
import requests
from googletrans import Translator
from unidecode import unidecode

from google_images_download import google_images_download
from utils import smart_loader, smart_saver
from word_requests.urls_and_parsers import (
    DicioParser,
    LingueeParser,
    ReversoParser,
)

FROM_LANG = "pt"
TO_LANG = "de"
LANGUAGE = {"pt": "Portuguese", "de": "German", "en": "English", "es": "Spanish"}


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
    conj_table_html = attr.ib(default="")

    def __attrs_post_init__(self):
        parser_attrs = {
            "phrase": self.search_term,
            "from_lang": FROM_LANG,
            "to_lang": TO_LANG,
        }
        self.parsers = {
            "linguee": LingueeParser(**parser_attrs),
            "dicio": DicioParser(**parser_attrs),
            "reverso": ReversoParser(**parser_attrs),
        }

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
        for parser in self.parsers.values():
            self.update_from_dict(parser.result_dict(self.search_term))
            # url = URL_FUNCTIONS[site](self.search_term)
            # resp = requests.get(url)
            # parsed_resp = PARSE_FUNCTIONS[site](resp)
            # self.update_from_dict(parsed_resp)

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
    def from_json(cls, path):
        return cls(**smart_loader(path))

    def save_as_json(self, path=None):
        if path is None:
            path = f"data/{self.folder()}/{self.folder()}.json"
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        attribute_dict = {
            re.sub("^_", "", key): value
            for key, value in vars(self).items()
            if key != "parsers"
        }
        smart_saver(attribute_dict, path)

    # TODO: check if return value is important
    def search(self, new_search_term):
        self.search_term = new_search_term
        path = f"{self.data_dir}/{self.folder()}/{self.folder()}.json"
        if os.path.exists(path):
            try:
                attribute_dict = smart_loader(path)
                self.__init__(**attribute_dict)
                return True
            except (TypeError, AttributeError):
                print("Could not load previously saved file. Fetching data again...")
        self.request_data()
        self.request_img_urls()
        self.add_translations()
        self.save_as_json()
        return True


if __name__ == "__main__":
    q = Word(search_term="mesa")
    print(q)
    q.search("casa")
    print(q)
