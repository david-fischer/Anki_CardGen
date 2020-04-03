import os
import re
import subprocess

import attr
import requests
import wget
from bs4 import BeautifulSoup
from translate import Translator

# OTHER PYTHON FILES IN SAME DIR
from anki_scripts.add_card import add_image_card
from anki_scripts.linguee_query import ask, extract_info
from google_images_download import google_images_download

LINGUEE_API_BASE_URL = "https://linguee-api.herokuapp.com/api?q=%s&src=es&dst=%s"
AUDIO_BASE_URL = "http://www.linguee.de/mp3/%s.mp3"
SYNONYM_BASE_URL = "http://www.wordreference.com/sinonimos/%s"
FROM_LANG = "pt"
TO_LANG = "de"
LANGUAGE = {"pt": "Portuguese", "de": "German", "en": "English", "es": "Spanish"}

translator = Translator(from_lang=FROM_LANG, to_lang=TO_LANG)


def request_synonyms(word):
    """
    If possible, uses SYNONYM_BASE_URL to find synonyms and returns as list.
    Returns None, when the response was empty.
    :param word:
    :return list_of_synonyms:
    """
    url = SYNONYM_BASE_URL % word
    soup = BeautifulSoup(requests.get(url).text)
    try:
        return soup.find_all(class_="trans clickable")[0].find_all("li")[0].text.split(",")
    except IndexError:
        print("could not find synonyms :(")
        return None


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
    url_dict = attr.ib(default={"audio_base": AUDIO_BASE_URL,
                                "linguee_api_base": LINGUEE_API_BASE_URL,
                                "synonym_base": SYNONYM_BASE_URL,
                                })
    # word properties
    type = attr.ib(default="")  # phrase or word
    word_type = attr.ib(default="")  # verb noun etc
    gender = attr.ib(default="")
    audio_url = attr.ib(default="")
    examples = attr.ib(default=[])
    synonyms = attr.ib(default=[])
    translated = attr.ib(default="")
    trans_syns = attr.ib(default=[])
    image_urls = attr.ib(default=[""])
    # other
    anki_user = attr.ib(default="new_user")
    output_path = attr.ib(default=".")
    folder = attr.ib(default="")

    def __attrs_post_init__(self):
        self.search_term = self.search_term.strip().lower()
        self.type = 'phrase' if ' ' in self.search_term else 'word'
        self.folder = self.search_term.replace(" ", "_")
        os.makedirs(self.folder, exist_ok=True)
        self.synonyms = [syn for syn in request_synonyms(self.search_term) if syn != ""]
        self.trans_syns = [translator.translate(syn) for syn in self.synonyms]
        self.image_urls = self.request_img_urls()
        self.linguee_query()
        self.audio_url = self.url_dict["audio_base"] % self.audio_url
        self.download_audio()

    def set_api_url(self, url):
        self.url_dict["linguee_api_base"] = url

    # GETTING DATA
    def linguee_query(self):
        qry_str = self.search_term.replace(" ", "+")
        response = ask(qry_str, self.url_dict["linguee_api"])
        if self.type == "phrase":
            self.translated, self.audio_url, _, _, self.examples = extract_info(response)
        else:
            self.translated, self.audio_url, self.word_type, self.gender, self.examples = extract_info(response)

    def download_audio(self):
        wget.download(self.audio_url, f"{self.folder}/{self.folder}.mp3")

    def request_img_urls(self):
        """
        Downloads the thumbnails of the first 10 results from a Google Image search.
        Renames the thumbnails into 1.jpg - 10.jpg.
        Returns list of the urls of the images corresponding the thumbnails
        :return:list
        """
        response = google_images_download.googleimagesdownload()
        arguments = {"keywords": self.search_term,
                     "output_directory": self.search_term,
                     "no_directory": True,
                     "limit": 10,
                     "format": "jpg",
                     "language": LANGUAGE[FROM_LANG],
                     "thumbnail_only": True,
                     "print_urls": True,
                     "prefix": "img_",
                     "save_source": "source",
                     }
        paths = response.download(arguments)[0][self.search_term]
        with open(f"{self.search_term}/source.txt") as file:
            thumbnails = [line.split("\t")[0] for line in file]
            for count, thumb in enumerate(thumbnails):
                try:
                    os.rename(thumb, f"{self.folder}/thumb_{count}.jpg")
                except FileNotFoundError:
                    print(str(count) + " not found")
            os.rmdir(f"{self.search_term}/ - thumbnail")
            os.remove(f"{self.folder}/source.txt")
        return paths

    # GETTING USER INPUT
    # field_list = yad_args(path=self.output_path,
    #                       search_term=self.search_term,
    #                       translated=self.translated,
    #                       folder=self.folder,
    #                       gender=self.gender,
    #                       synonyms=self.synonyms,
    #                       examples=self.examples)

    # GENERATE ANKI CARDS FROM DATA

    def mark_examples(self):
        for word in self.search_term.split(" "):
            self.examples = [re.sub(r'((?i)%s)' % word, r'<font color=red><b>\1</font></b>', ex) for ex in
                             self.examples]

    def generate_card(self):
        syn_str = ", ".join(self.synonyms)
        ex_str = html_list(self.examples)
        hint_str = self.translated.replace("\n", "<br />")
        add_image_card(word=self.search_term,
                       file=self.folder,
                       synonyms=syn_str,
                       hint=hint_str,
                       examples=ex_str)

    # ADD CARD TO DECK OR DECK TO ANKI-APP

    def import_card_to_deck(self):
        print("Importing Card to Deck")
        subprocess.call(["bash -c \" timeout 3 anki -p %s %s/output.apkg \" " % (self.anki_user, self.output_path)],
                        shell=True)
        print("Finished")
