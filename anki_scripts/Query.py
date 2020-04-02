import argparse
import os
import re
import subprocess

import attr
import requests
import wget
import yad
from bs4 import BeautifulSoup
from translate import Translator
from unidecode import unidecode as remove_accents

# OTHER PYTHON FILES IN SAME DIR
from anki_scripts.add_card import add_image_card
from anki_scripts.linguee_query import ask, extract_info
from anki_scripts.yad_args import yad_args, yad_img_args
from google_images_download import google_images_download

FROM_LANG = "pt"
TO_LANG = "de"
LANGUAGE = {"pt": "Portuguese", "de": "German", "en": "English", "es": "Spanish"}
translator = Translator(from_lang=FROM_LANG, to_lang=TO_LANG)


def es_to_de(string):
    return translator.translate(remove_accents(string))


yad = yad.YAD()
bash_script_path = "~/python_scripts/anki_scripts/"


def get_soup_object(url):
    return BeautifulSoup(requests.get(url).text)


# noinspection PyBroadException
def synonyms(word):
    url = "http://www.wordreference.com/sinonimos/%s" % word
    soup = get_soup_object(url)
    try:
        results = soup.find_all(class_="trans clickable")[0].find_all("li")[0]
        return results.text
    except:
        print("could not find synonyms :(")
        return ""


def html_list(str_list):
    start = "<ul>\n"
    end = "</ul>\n"
    middle = ["<li type=\"square\">" + item + "</li>\n" for item in str_list]
    return start + "".join(middle) + end


# noinspection PyBroadException
@attr.s
class Query:
    # query properties
    search_term = attr.ib(default="casa")
    url_dict = attr.ib(default={"audio_base": "http://www.linguee.de/mp3/%s.mp3",
                                "linguee_api": "https://linguee-api.herokuapp.com/api?q=%s&src=es&dst=%s"
                                })
    response = attr.ib(default=[], repr=False)
    # word properties
    type = attr.ib(default="")  # phrase or word
    word_type = attr.ib(default="")  # verb noun etc
    gender = attr.ib(default="")
    audio_link = attr.ib(default="")
    examples = attr.ib(default=[])
    synonyms = attr.ib(default=[])
    translated = attr.ib(default="")
    trans_syns = attr.ib(default=[])
    # other
    anki_user = attr.ib(default="new_user")
    output_path = attr.ib(default=".")
    folder = attr.ib(default="")

    def __attrs_post_init__(self):
        self.search_term = self.search_term.strip().lower()
        self.folder = self.search_term.replace(" ", "_")

    def translate(self):
        translations = [x["translations"] for x in self.response["exact_matches"]]
        translations = [[x["text"] for x in y] for y in translations]
        translation_string = "\n".join([", ".join(x) for x in translations])
        # print(translation_string)
        self.translated = translation_string

    def linguee_query(self):
        self.word_or_phrase()
        qry_str = self.search_term.replace(" ", "+")
        # print(qry_str)
        self.response = ask(qry_str, self.url_dict["linguee_api"])
        # print(extract_info(self.response))
        # print(ask(qry_str))
        if self.type == "phrase":
            # print("phrase",qry_str)
            self.audio_link, b, c, self.examples = extract_info(self.response)
        else:
            self.audio_link, self.word_type, self.gender, self.examples = extract_info(self.response)
        # response=html_response
        # change languages
        # yad: Let user know if not possible to connect
        # yad: Let user know if no matches

    def word_or_phrase(self):
        # single word or phrase?
        if " " in self.search_term:
            # print("SPACE")
            self.type = "phrase"

    def print_all(self):
        print("-----------------------------------------------")
        print("Search term: %s" % self.search_term)
        print("Folder: %s" % self.folder)
        print("Type : %s" % self.type)
        print("Synonyms: %s" % self.synonyms)
        print("Audio Link: %s" % self.audio_link)
        print("Example:%s" % self.examples)
        print("-----------------------------------------------")

    def download_images(self):
        response = google_images_download.googleimagesdownload()
        arguments = {"keywords": self.search_term,
                     "output_directory": self.search_term,
                     # "image_directory": "casa",
                     "no_directory": True,
                     "limit": 20,
                     "format": "jpg",
                     "language": LANGUAGE[FROM_LANG],
                     "thumbnail_only": True,
                     "print_urls": True,
                     # "print_paths":True,
                     "prefix": "img_",
                     "save_source": "source",
                     }
        paths = response.download(arguments)[0][self.search_term]
        print(len(paths))
        with open(f"{search_term}/source.txt") as file:
            thumbnails = [line.split("\t")[0] for line in file]
            for count,thumb in enumerate(thumbnails):
                try:
                    os.rename(thumb,f"{self.folder}/thumb_{count}.jpg")
                except(FileNotFoundError):
                    print(str(count) + " not found")
            os.rmdir(f"{self.search_term}/ - thumbnail")
            os.remove(f"{self.folder}/source.txt")
        return paths


    def set_synonyms(self):
        self.synonyms = synonyms(self.search_term).split(",")
        self.synonyms = [syn for syn in self.synonyms if syn != ""]
        self.trans_syns = ["" for _ in self.synonyms]

    def download_audio(self):
        audio_url = self.url_dict["audio_base"] % self.audio_link
        print("Downloading audio-file...")
        wget.download(audio_url, f"{self.folder}/{self.folder}.mp3")

    def check_attributes(self):
        # starts yad to let user check stuff
        field_list = yad_args(path=self.output_path,
                              search_term=self.search_term,
                              translated=self.translated,
                              folder=self.folder,
                              gender=self.gender,
                              synonyms=self.synonyms,
                              examples=self.examples)
        # for x in field_list:
        #     print(x)
        user_input = yad.Form(center=1, on_top=1, fields=field_list)

        if user_input is None or user_input['rc'] != 0:
            print("Abbruch")
        else:
            user_input.pop("rc")
        if user_input[1] != "-":
            self.search_term = user_input[1] + " " + user_input[2]
        else:
            self.search_term = user_input[1]
        sl = len(self.synonyms)
        el = len(self.examples)
        for i in reversed(range(sl)):
            # print(i+3)
            if user_input[i + 2] == "FALSE":
                del self.synonyms[i]
        for i in reversed(range(el)):
            if user_input[i + 2 + sl] == "FALSE":
                del self.examples[i]

    def choose_image(self):
        yad.Form(center=1, on_top=1,
                 fields=yad_img_args(path=self.output_path, folder=self.folder, images=["1.jpg", "2.jpg", "3.jpg"]))

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

    def get_all_data(self):
        os.makedirs(self.folder, exist_ok=True)
        path_list = self.download_images()
        self.set_synonyms()
        # print(self.url_dict)
        # noinspection PyBroadException
        try:
            print("trying..." + self.url_dict["linguee_api"])
            self.linguee_query()
        except:
            print("trying instead: " + "http://localhost:8000/api?q=%s&src=es&dst=%s")
            self.set_api_url("http://localhost:8000/api?q=%s&src=es&dst=%s")
            self.linguee_query()
        try:
            self.translate()
        except:
            print("Could not find translation.")
        self.download_audio()
        self.check_attributes()
        self.choose_image()
        self.mark_examples()

    def import_card_to_deck(self):
        print("Importing Card to Deck")
        subprocess.call(["bash -c \" timeout 3 anki -p %s %s/output.apkg \" " % (self.anki_user, self.output_path)],
                        shell=True)
        print("Finished")
        # print("Download finished.")

    def set_api_url(self, url):
        self.url_dict["linguee_api"] = url


def main(search):
    query = Query(search)
    query.get_all_data()
    # query.print_all()
    # print(query)
    # dfg query.generate_card()
    # dsfg  query.import_card_to_deck()


# stuff only to run when not called via 'import' here
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Adds Anki card to test_deck")
    parser.add_argument('--word', type=str, help="the search word")
    parser.add_argument('--api', type=str, help="the url of the api")
    args = parser.parse_args()
    search_term = args.word if args.word is not None else "casa"

    if args.api is None:
        api_url = "https://linguee-api.herokuapp.com/api?q=%s&src=es&dst=%s"
    else:
        api_url = args.api

    main(search_term)
