import functools
import operator
import os

import spacy
from bs4 import BeautifulSoup
from kivymd.app import MDApp

COLOR2MEANING = {
    "highlight_yellow": "words",
    "highlight_blue":   "phrases",
    "highlight_purple": "sentences",
    "highlight_orange": "",
}
MEANING2COLOR = {val: key for key, val in COLOR2MEANING.items()}

try:
    nlp = spacy.load("pt_core_news_sm-2.2.5/pt_core_news_sm/pt_core_news_sm-2.2.5")
except OSError:
    nlp = spacy.load("../pt_core_news_sm-2.2.5/pt_core_news_sm/pt_core_news_sm-2.2.5")


# GENERAL

class CD:
    """Context manager for changing the current working directory"""

    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


# KIVY

def widget_by_id(string):
    """
    :arg string: "/edit_tab/word_prop/translation_chips
    :returns widget root.ids.edit_tab.ids.word_prop ... usw
    """
    ids = string.split("/")
    ids = [id for id in ids if id != ""]
    obj = MDApp.get_running_app().root
    for id in ids:
        try:
            obj = getattr(obj.ids, id)
        except:
            obj = obj.ids.screen_man.get_screen(id).children[0]
    return obj


def selection_helper(base, id=None, props=["text"]):
    base_obj = getattr(base.ids, id) if id is not None else base
    out = [base_obj.get_checked(property=prop) for prop in props]
    return functools.reduce(operator.iconcat, out, [])


# KINDLE EXPORT PARSING

def dict_from_kindle_export(file_path):
    with open(file_path, "r") as file:
        soup = BeautifulSoup(file, "lxml")
    headings = soup.select("div.noteHeading span")
    temp_dict = {
        # key = word : value = color_of_highlighting
        heading.find_next().text: heading["class"][0]
        for heading in headings
    }
    dict = {val: [] for val in temp_dict.values()}
    for key, val in temp_dict.items():
        key = key.strip()
        dict[val].append(key)
    # print(dict.keys())
    return dict


def clean_up(words, remove_punct=True, lower_case=True, lemmatize=True):
    if remove_punct:
        words = [word.strip(",.;:-–—!?¿¡\"\'") for word in words]
    if lower_case:
        words = [word.lower() for word in words]
    if lemmatize:
        lemmas = [" ".join([lemma.lemma_]) for word in words for lemma in nlp(word)]
    for word, lemma in zip(words, lemmas):
        if word != lemma:
            print(word, lemma)
    return words


def word_list_from_kindle(path):
    color = MEANING2COLOR["words"]
    word_list = dict_from_kindle_export(path)[color]
    word_list = clean_up(word_list)
    return word_list


if __name__ == "__main__":
    out = word_list_from_kindle("test/test_data/Portuguese Short Stories for Beginners 20 Captiva - Notizbuch.html")
