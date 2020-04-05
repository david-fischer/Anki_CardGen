import os
import re
import subprocess
import attr
import wget

from translate import Translator

# OTHER PYTHON FILES IN SAME DIR
from anki_scripts.add_card import add_image_card
from anki_scripts.dictionary_queries import ask, extract_info, request_synonyms_from_wordref, request_data_from_linguee, \
    request_data_from_dicio
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
    translated = attr.ib(default="")
    trans_syns = attr.ib(default=[])
    image_urls = attr.ib(default=[""])
    audio_url = attr.ib(default="")
    add_info_dict = attr.ib(default={})
    # other
    anki_user = attr.ib(default="new_user")
    output_path = attr.ib(default=".")
    folder = attr.ib(default="")

    def get_data(self):
        self.search_term = self.search_term.strip().lower()
        self.folder = self.search_term.replace(" ", "_")
        os.makedirs(self.folder, exist_ok=True)
        self.image_urls = self.request_img_urls()
        self.request_dict_data()
        self.download_audio()

    #a def set_api_url(self, url):
    #a     """
    #a     changes the api-url (this might be necessary if to many requests have been made).
    #a     :param url:
    #a     """
    #a     self.url_dict["linguee_api_base"] = url

    # GETTING DATA
    def request_dict_data(self):
        """
        Uses ask from dictionary_queries.py to fill the fields:
        self.translated
        self.audio_url
        self.word_type
        self.gender
        self.examples
        """
        self.translated, \
        self.audio_url, \
        self.word_type, \
        self.gender, \
        self.examples \
            = request_data_from_linguee(self.search_term,FROM_LANG)
        self.explanations, \
        self.synonyms, \
        self.antonyms, \
        add_examples, \
        self.add_info_dict = request_data_from_dicio(self.search_term)
        self.examples += add_examples

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
        """
        Highlights the search_word in the example sentences using css.
        """
        for word in self.search_term.split(" "):
            self.examples = [re.sub(r'((?i)%s)' % word, r'<font color=red><b>\1</font></b>', ex) for ex in
                             self.examples]

    def generate_card(self):
        """
        Calls add_image_card to generate a card from the obtained data.
        The card is saved in output.apkg in the working dir.
        """
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
        """
        Adds the output.apk file to the user self.anki_user
        """
        print("Importing Card to Deck")
        subprocess.call(["bash -c \" timeout 3 anki -p %s %s/output.apkg \" " % (self.anki_user, self.output_path)],
                        shell=True)
        print("Finished")



if __name__ == "__main__":
    q = Query(search_term="mesa")
    print(q)