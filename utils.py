import csv
import functools
import operator
import os
from collections import defaultdict
from datetime import datetime

try:
    import spacy

    SPACY_IS_AVAILABLE = True
except ModuleNotFoundError:
    print("Spacy is not available, fall back to limited version. "
          "This means, words will not be lemmatized in the clean-up")
    SPACY_IS_AVAILABLE = False

from bs4 import BeautifulSoup
from kivymd.app import MDApp

COLOR2MEANING = {
    "highlight_yellow": "words",
    "highlight_blue":   "phrases",
    "highlight_pink":   "sentences",
    "highlight_orange": "",
}
MEANING2COLOR = {val: key for key, val in COLOR2MEANING.items()}

nlp = None


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


def save_dict_to_csv(dict, out_path):
    is_first_entry = not os.path.exists(out_path)
    with open(out_path, "a") as file:
        writer = csv.DictWriter(file, fieldnames=dict.keys())
        if is_first_entry:
            writer.writeheader()
        writer.writerow(dict)


def load_dict_from_csv(path):
    with open(path, 'r') as read_obj:
        return list(csv.DictReader(read_obj))


def now_string():
    return str(datetime.now()).split(".")[0].replace(" ", "_")


# KIVY

def set_screen(screen_name):
    widget_by_id("screen_man").current = screen_name


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


def selection_helper(base, id=None, props=None):
    if props is None:
        props = ["text"]
    base_obj = getattr(base.ids, id) if id is not None else base
    out = [base_obj.get_checked(property=prop) for prop in props]
    return functools.reduce(operator.iconcat, out, [])


# KINDLE EXPORT PARSING

def dict_from_kindle_export(file_path):
    with open(file_path, "r") as file:
        soup = BeautifulSoup(file, "lxml")
    heading_tags = soup.select("div.noteHeading span")
    highlight_dict = defaultdict(list)
    for tag in heading_tags:
        highlight_dict[tag["class"][0]].append(tag.find_next().text.strip())
    return highlight_dict


def clean_up(words, remove_punct=True, lower_case=True, lemmatize=True):
    if remove_punct:
        words = [word.strip(",.;:-–—!?¿¡\"\'") for word in words]
    if lower_case:
        words = [word.lower() for word in words]
    if lemmatize:
        if SPACY_IS_AVAILABLE:
            global nlp
            if nlp is None:
                nlp = spacy.load("pt_core_news_sm")
            words = [" ".join([lemma.lemma_]) for word in words for lemma in nlp(word)]
        else:
            print("Lemmatization skipped. Spacy modul is not installed.")
    return words


def word_list_from_kindle(path):
    color = MEANING2COLOR["words"]
    return dict_from_kindle_export(path)[color]


if __name__ == "__main__":
    out = word_list_from_kindle("test/test_data/Portuguese Short Stories for Beginners 20 Captiva - Notizbuch.html")
