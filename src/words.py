"""Implementation of :class:`Word`."""
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
    Class that fetches all data for a given search_term.

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
        """Getter function for :attr:`_audio_url`."""
        return self._audio_url

    @audio_url.setter
    def audio_url(self, value):
        """Set :attr:`_audio_url` and download file."""
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
        """Return :attr:`search_term` in lower case and with special characters replaced."""
        return unidecode(self.search_term).lower()

    def folder(self):
        """Return result from :meth:`search_term_utf8` with spaces replaced by underscores."""
        return self.search_term_utf8().replace(" ", "_")

    def base_path(self):
        """Return ``f"{self.data_dir}/{self.folder()}/{self.folder()}"``. Used as base to save files."""
        return f"{self.data_dir}/{self.folder()}/{self.folder()}"

    def translate(self, string):
        """Translate string from :attr:`from_lang` to :attr:`to_lang`."""
        return translator.translate(string, src=self.from_lang, dest=self.to_lang).text

    def request_data(self):
        """Get result from parsers in :attr:`parsers` and pass results to :meth:`update_from_dict`."""
        for parser in self.parsers.values():
            self.update_from_dict(parser.result_dict(self.search_term))

    def update_from_dict(self, attr_dict):
        """
        Update :class:`Word` s attributes by iterating through ``attr_dict``.

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
        """Add translations to attributes ["examples", "explanations", "synonyms", "antonyms"], if necessary."""
        for key in ["examples", "explanations", "synonyms", "antonyms"]:
            values = getattr(self, key)
            for i, val in enumerate(values):
                if isinstance(val, str):
                    values[i] = [val, self.translate(val)]
                elif isinstance(val, list) and len(val) == 1:
                    values[i] = [val[0], self.translate(val[0])]
            setattr(self, key, values)

    def request_img_urls(self, keywords=None):
        """
        Use :class:`parsers.Parser` at :attr:`parsers` ["google_image_parser"] to get image urls.

        Args:
            keywords:
                String for image search. (Default value = None)
                If not set, defaults to :attr:`search_term`.
        Returns:
            List of img_urls.
        """
        if keywords is None:
            keywords = self.search_term
        return self.parsers["google_images"].result_dict(keywords)["image_urls"]

    def mark_examples(self):
        """Highlights the search_word in the example sentences using css."""
        for word in self.search_term.split(" "):
            self.examples = [
                re.sub(r"((?i)%s)" % word, r"<font color=red><b>\1</font></b>", ex)
                for ex in self.examples
            ]

    @classmethod
    def from_json(cls, path):
        """Initialize :class:`Word` from dictionary saved as .json."""
        return cls(**smart_loader(path))

    def save_as_json(self, path=None):
        """
        Save class attributes as dictionary in a .json-file.

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

    def get_fix_card_dict(self):
        """Return the part of the data for the anki-card, that does not depend on the user-choice."""
        media_files = [f"{self.base_path()}.{ext}" for ext in ["jpg", "mp3"]]
        media_files = [path for path in media_files if os.path.exists(path)]
        return {
            "word": self.search_term,
            "image": f'<img src="{self.folder()}.jpg">',
            "audio": f"[sound:{self.folder()}.mp3]",
            "additional_info": str(self.add_info_dict),
            "conjugation_table": self.conj_table_html,
            "media_files": media_files,
        }

    # TODO: check if return value is important
    def search(self, new_search_term):
        """
        Load data for ``new_search_term``.

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
                self.add_translations()
                self.save_as_json()
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
