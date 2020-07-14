"""
Implementation of :class:`Word`.
"""
import os
import re

import attr
import requests
from googletrans import Translator
from unidecode import unidecode

from parsers import (
    DicioParser,
    GoogleImagesParser,
    LingueeParser,
    ReversoParser,
)
from utils import smart_loader, smart_saver

translator = Translator()


@attr.s(auto_attribs=True)
class Word:
    """
    Class that fetches and edits the words that makes up the choices, presented to the user in the card-generation
    process.

    Main function is :meth:`search` function.
    """

    # word properties
    search_term: str = ""
    word_type: str = ""  # verb noun etc
    gender: str = ""
    examples: list = []
    explanations: list = []
    synonyms: list = []
    antonyms: list = []
    translations: list = []
    trans_syns: list = []
    image_urls: list = []
    _audio_url: str = ""
    add_info_dict: dict = {}
    conj_table_html: str = ""
    # query properties
    data_dir: str = "../app_data/words"
    from_lang: str = "pt"
    to_lang: str = "de"

    def __attrs_post_init__(self):
        parser_attrs = {
            "phrase": self.search_term,
            "from_lang": self.from_lang,
            "to_lang": self.to_lang,
        }
        self.parsers = {
            "linguee": LingueeParser(**parser_attrs),
            "dicio": DicioParser(**parser_attrs),
            "reverso": ReversoParser(**parser_attrs),
            "google_images": GoogleImagesParser(**parser_attrs),
        }

    @property
    def audio_url(self):
        """Getter function for :attr:`_audio_url`"""
        return self._audio_url

    @audio_url.setter
    def audio_url(self, value):
        """
        When the :attr:`_audio_url` is set, downloads the file.
        """
        self._audio_url = value
        if not value:
            return
        print(f"start downloading audio from {value}...")
        response = requests.get(value, allow_redirects=True)
        os.makedirs(f"{self.data_dir}/{self.folder()}", exist_ok=True)
        with open(f"{self.base_path()}.mp3", "wb") as file:
            file.write(response.content)
        print("audio download complete.")

    def search_term_utf8(self):
        """
        Returns:
          : :attr:`search_term` with special characters replaced.
        """
        return unidecode(self.search_term).lower()

    def folder(self):
        """
        Used as folder name to save files to.

        Returns:
          : :method:`search_term_utf8` with spaces replaced by underscores.
        """
        return self.search_term_utf8().replace(" ", "_")

    def base_path(self):
        """
        Used as base to save files.

        Returns:
            `f"{self.data_dir}/{self.folder()}/{self.folder()}"'
        """
        return f"{self.data_dir}/{self.folder()}/{self.folder()}"

    def translate(self, string):
        """
        Translates string from :attr:`from_lang` to :attr:`to_lang`.

        Returns:
            : Translated string.
        """
        return translator.translate(string, src=self.from_lang, dest=self.to_lang).text

    def request_data(self):
        """Iterates through parsers and passes results to :meth:`update_from_dict`"""
        for parser in self.parsers.values():
            self.update_from_dict(parser.result_dict(self.search_term))

    def update_from_dict(self, attr_dict):
        """
        Iterates through attr_dict and updates :class:`Word` attributes.

        If the value is a list, it extends the original list, else the value is set to the value of attr_dict

        Args:
          attr_dict:
            Each key should be the name of an attribute of :class:`Word`, the value corresponds to the updated value.
        """
        for key, value in attr_dict.items():
            old_val = getattr(self, key)
            if isinstance(old_val, list):
                value = old_val + value
            setattr(self, key, value)

    def add_translations(self):
        """
        For the attributes ["examples", "synonyms", "antonyms"], it iterates to the corresponding lists and adds
        translations, where none are already present.
        """
        for key in ["examples", "synonyms", "antonyms"]:
            values = getattr(self, key)
            for i, val in enumerate(values):
                if isinstance(val, str):
                    values[i] = [val, self.translate(val)]
                elif isinstance(val, list) and len(val) == 1:
                    values[i] = [val[0], self.translate(val[0])]
            setattr(self, key, values)

    def request_img_urls(self, keywords=None):
        """

        Args:
            keywords:
                String for image search. (Default value = None)
                If not set, defaults to :attr:`search_term`.
        Returns:
            List of img_urls.
        """
        if keywords is None:
            keywords = self.search_term
        return self.parsers["google_images"].result_dict(keywords)["img_urls"]

    def mark_examples(self):
        """Highlights the search_word in the example sentences using css."""
        for word in self.search_term.split(" "):
            self.examples = [
                re.sub(r"((?i)%s)" % word, r"<font color=red><b>\1</font></b>", ex)
                for ex in self.examples
            ]

    @classmethod
    def from_json(cls, path):
        """
        Initializes :class:`Word` from dictionary saved as .json.
        """
        return cls(**smart_loader(path))

    def save_as_json(self, path=None):
        """
        Saves class attributes as dictionary in a .json-file.

        Args:
          path: If None, is set to f"words/{self.folder()}/{self.folder()}.json" (Default value = None)
        """
        if path is None:
            path = f"{self.base_path()}.json"
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
        """
        If possible loads from previously saved search.
        If not, uses the parsers to obtain info and adds translations, then saves the result for future searches.

        Args:
          new_search_term:
        """
        self.search_term = new_search_term
        path = f"{self.base_path()}.json"
        if os.path.exists(path):
            try:
                attribute_dict = smart_loader(path)
                self.__init__(**attribute_dict)
                return
            except (TypeError, AttributeError):
                print("Could not load previously saved file. Fetching words again...")
        self.__init__(search_term=self.search_term.strip().lower())
        self.request_data()
        self.add_translations()
        self.save_as_json()


if __name__ == "__main__":
    q = Word("casa")
    print(q)
    q.search("casa")
    print(q)
