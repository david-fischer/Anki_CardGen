"""
This module contains lots of helper functions.
"""

import csv
import functools
import json
import operator
import os
import pickle
import re
import shutil
from collections import defaultdict
from datetime import datetime
from glob import glob
from time import sleep

import imgkit
import pystache
from bs4 import BeautifulSoup
from kivy.clock import mainthread
from kivy.core.image import Image as KivyImage
from kivy.core.window import Window
from kivy.graphics.context_instructions import Scale, Translate
from kivy.graphics.fbo import Fbo
from kivy.graphics.gl_instructions import ClearBuffers, ClearColor
from kivymd.app import MDApp
from PIL import Image

try:
    import spacy

    SPACY_IS_AVAILABLE = True
    """``True`` if spacy could be imported, else ``False``"""
except ModuleNotFoundError:
    print(
        "Spacy is not available, fall back to limited version. "
        "This means, words will not be lemmatized in the clean-up"
    )
    SPACY_IS_AVAILABLE = False

COLOR2MEANING = {
    "highlight_yellow": "words",
    "highlight_blue": "phrases",
    "highlight_pink": "sentences",
    "highlight_orange": "",
}
"""
Dictionary relating highlight colors to the things that are highlighted with them.
Currently only ``COLOR2MEANING["highlight_yellow"] = "words"`` is used.
"""
MEANING2COLOR = {val: key for key, val in COLOR2MEANING.items()}

nlp = None  # pylint: disable = invalid-name


# GENERAL


class CD:
    """Context manager for changing the current working directory to :attr:`new_path`."""

    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)
        self.saved_path = None

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


def save_dict_to_csv(some_dict, out_path):
    """
    Saves dictionary as row to csv.
    """
    is_first_entry = not os.path.exists(out_path)
    with open(out_path, "a") as file:
        writer = csv.DictWriter(file, fieldnames=some_dict.keys())
        if is_first_entry:
            writer.writeheader()
        writer.writerow(some_dict)


def load_dicts_from_csv(path):
    """
    Loads csv. Has to have the keys as first line.

    Returns:
        : List of dictionaries.
    """
    with open(path, "r") as read_obj:
        return list(csv.DictReader(read_obj))


def smart_loader(path):
    """
    Uses file ending of path to determine which function to use to load file.

    Supported file endings:
        * .p (pickle)
        * .csv
        * .json

    Args:
      path: Path of file to load.

    Returns:
      : Loaded object.
    """
    ext = path.split(".")[-1]
    if ext == "p":
        with open(path, "rb") as file:
            return pickle.load(file)
    with open(path, "r") as file:
        if ext == "json":
            return json.load(file)
        if ext == "csv":
            return load_dicts_from_csv(path)
    raise Exception


def smart_saver(obj, path):
    """
    Uses file ending of path to determine which function to use to save file.

    Supported file endings:
        * .p (pickle)
        * .csv
        * .json

    Args:
      obj: Object to save.
      path: Path where object should be stored.

    """
    ext = path.split(".")[-1]
    if ext == "p":
        with open(path, "wb") as file:
            pickle.dump(obj, file)
    if ext == "json":
        with open(path, "w") as file:
            json.dump(obj, file, indent=4, sort_keys=True)
    if ext == "csv":
        save_dict_to_csv(obj, path)


def now_string():
    """

    Returns:
      : Current time in the format ``YYYY-MM-DD_HH:MM:SS``.
    """
    return str(datetime.now()).split(".")[0].replace(" ", "_")


# KIVY


def set_screen(screen_name):
    """
    Sets current screen to the one with name ``screen_name``.
    """
    widget_by_id("screen_man").current = screen_name


def widget_by_id(string):
    """
    Get widget by string of ids, seperated by "/".

    Args:
      string: Stings of ids, seperated by "/". The first one can be a screen name.

    Returns:
      : widget

    Examples
      >>> widget_by_id("screen_single_word/edit_tab/word_prop")
      MDApp.get_running_app().root.ids.screen_man.get_screen("screen_single_word").children[
      0].ids.word_prop
    """
    id_list = string.split("/")
    id_list = [id_str for id_str in id_list if id_str != ""]
    obj = MDApp.get_running_app().root
    if id_list[0] in obj.ids.screen_man.screen_names:
        obj = obj.ids.screen_man.get_screen(id_list.pop(0)).children[0]
    for id_str in id_list:
        obj = getattr(obj.ids, id_str)
    return obj


def sleep_decorator(time):
    """
    Executes sleep(time) before and after decorated function.
    """

    def the_real_decorator(function):
        def wrapper(*args, **kwargs):

            sleep(time)
            function(*args, **kwargs)
            sleep(time)

        return wrapper

    return the_real_decorator


@sleep_decorator(1)
@mainthread
def screenshot(path):
    """
    Takes screenshot of the current state of the app and saves it under ``path``.

    The sleep- and mainthread-decorator ensure that the app shows the current state properly.
    """
    root_widget = MDApp.get_running_app().root

    fbo = Fbo(size=(root_widget.width, root_widget.height), with_stencilbuffer=True,)

    with fbo:
        ClearColor(*MDApp.get_running_app().theme_cls.bg_normal)
        ClearBuffers()
        Scale(1, -1, 1)
        Translate(-root_widget.x, -root_widget.y - root_widget.height, 0)

    fbo.add(root_widget.canvas)
    fbo.draw()
    img = KivyImage(fbo.texture)

    img.save(path)


def make_screenshots(window_size=(270 * 1.4, 480 * 1.4)):
    """Set the app in a number of predefined states and takes a screenshot of each."""
    old_size = Window.size
    Window.size = window_size
    for item in widget_by_id("drawer_list").children:
        item.on_release()
        screenshot(f"screenshots/{item.screen_name}.png")
    widget_by_id("nav_drawer").set_state("open")
    screenshot("../screenshots/nav_drawer_open.png")
    widget_by_id("nav_drawer").set_state("close")
    # Word
    word_prop = widget_by_id("screen_single_word/edit_tab/word_prop/")
    word_prop.ids.search_field.text = "casa"
    word_prop.load_or_search("casa")
    screenshot("../screenshots/example_word_text.png")
    tabs = widget_by_id("screen_single_word/tabs")
    tabs.carousel.index = 1  # (tabs.carousel, 1)
    screenshot("../screenshots/example_word_images.png")
    Window.size = old_size


rend = pystache.Renderer(escape=lambda s: s)


def save_card_pngs(word="casa", size=(540, 960)):
    """
    Saves pngs of the anki-cards for a given word, for which a card has to be generated earlier.

    Args:
      word:  (Default value = "casa")
      size:  (Default value = (540,960))
    """
    paths = glob("anki/*.html")
    field_dict = smart_loader(f"../app_data/words/{word}/{word}_card.json")
    field_dict["Audio"] = "&#9658;"
    try:
        shutil.copytree("anki/js", "/tmp/js/")
        shutil.copytree("anki/css", "/tmp/css/")
    except FileExistsError:
        print("JS AND CSS FOLDER ALREADY EXIST IN /tmp/ skip copying.")
    shutil.copy2(f"../app_data/words/{word}/{word}.jpg", f"/tmp/{word}.jpg")
    compress_img(f"/tmp/{word}.jpg", width=int(size[0]) - 12)
    os.makedirs(f"../screenshots/{word}", exist_ok=True)
    for path in paths:
        with open(path, "r") as file:
            string = file.read()
            string = rend.render(string, **field_dict)
        imgkit.from_string(
            string,
            f'../screenshots/{word}/{os.path.basename(path).replace(".html",".png")}',
            options={"width": int(size[0]), "height": int(size[1]),},
        )


def selection_helper(base, id_str=None, props=None):
    """

    Args:
      base:
      id_str:  (Default value = None)
      props:  (Default value = None)

    Returns:

    """
    if props is None:
        props = ["text"]
    base_obj = getattr(base.ids, id_str) if id_str is not None else base
    out = [base_obj.get_checked(property_name=prop) for prop in props]
    return functools.reduce(operator.iconcat, out, [])


# KINDLE EXPORT PARSING


def dict_from_kindle_export(file_path):
    """
    Extracts highlighted parts and sorts them by color in a dictionary.

    Args:
      file_path: Path to an html-file exported from kindle.

    Returns:
        :Dictionary `{"highlight_color_1" : ["list", "of" , "highlighted parts", ...],...}`
    """
    with open(file_path, "r") as file:
        soup = BeautifulSoup(file, "lxml")
    heading_tags = soup.select("div.noteHeading span")
    highlight_dict = defaultdict(list)
    for tag in heading_tags:
        highlight_dict[tag["class"][0]].append(tag.find_next().text.strip())
    return highlight_dict


def clean_up(words, remove_punct=True, lower_case=True, lemmatize=True):
    """
    Preprocess a list of words (or phrases).

    Args:
      words: List of words
      remove_punct: If True, removes trailing and leading punctuation. (Default value = True)
      lower_case: If True, converts everything to lower case. (Default value = True)
      lemmatize: If True, tries to convert each word to its dictionary-form. (Default value = True)

    Returns:
        : List of processed words (or phrases).
    """
    if remove_punct:
        words = [word.strip(",.;:-–—!?¿¡\"'") for word in words]
    if lower_case:
        words = [word.lower() for word in words]
    if lemmatize:
        if SPACY_IS_AVAILABLE:
            global nlp  # pylint: disable=global-statement,invalid-name
            if nlp is None:
                nlp = spacy.load("pt_core_news_sm")
            words = [" ".join([lemma.lemma_]) for word in words for lemma in nlp(word)]
        else:
            print("Lemmatization skipped. Spacy modul is not installed.")
    return words


def word_list_from_kindle(path):
    """
    Uses :const:`MEANING2COLOR` `["words"]` to extract the list of words highlighted in this specific color.

    Args:
      path: Path to html-file exported by kindle.

    Returns:
      : List of highlighted words.
    """
    color = MEANING2COLOR["words"]
    return dict_from_kindle_export(path)[color]


def word_list_from_txt(path):
    """
    Args:
      path: Path to txt-file. Each line should correspond to a word (or phrase).

    Returns:
      : List of words.
    """
    with open(path, "r") as file:
        words = file.read().splitlines()
    return words


def tag_word_in_sentence(sentence, tag_word):
    """
    Uses regex to wrap every derived form of a given ``tag_word`` in ``sentence`` in an html-tag.

    Args:
      sentence: String containing of multiple words.
      tag_word: Word that should be wrapped.

    Returns:
      : Sentence with replacements.
    """
    words = sentence.split()
    words = clean_up(words, lemmatize=False)
    # get unique, non-empty strings:
    words = [word for word in set(words) if word]
    lemmas = clean_up(words, lemmatize=True)
    print(words)
    print(lemmas)
    tag_lemma = clean_up([tag_word])[0]
    words_found = [
        word
        for word, lemma in zip(words, lemmas)
        if lemma == tag_lemma or word == tag_word
    ]
    for word in words_found:
        sentence = re.sub(
            f"([^>])({word})([^<])",
            r'\1<span class="word">\2</span>\3',
            sentence,
            flags=re.IGNORECASE,
        )
    return sentence


# Image resizing


def compress_img(path, width=512):
    """
    Uses the :class:`~PIL.Image` class to reduce the resolution of an image at ``path`` and overwrites it.

    If the image already has smaller width, nothing is done.

    Args:
      path: Path to image-file.
      width: New width of image (Default value = 512)
    """
    img = Image.open(path)
    if img.size[0] > width:
        resize = (width, width * img.size[1] // img.size[0])
        img = img.resize(resize, Image.ANTIALIAS)
    img.save(path, optimize=True)


if __name__ == "__main__":
    # pass
    # out = word_list_from_kindle("test/test_data/kindle_export.html")
    # print(out)
    # with open("test/test_data/words.txt", "w") as file:
    #     file.write("\n".join(out))

    # example = ("Construção em alvenaria usada como moradia, com distintos formatos ou tamanhos,"
    #            "normalmente térrea ou com dois andares. - Voltaire")
    # expl = ("Os homens que procuram a felicidade são como os embriagados que não conseguem encontrar a própria casa, "
    #         "apesar de saberem que a têm. Test Casas, casa, casa.")
    #
    # print(tag_word(expl, "casa"))
    # compress_img("screenshots/casa/casa.jpg")
    # save_card_htmls("casa")#
    save_card_pngs("comecar", size=(270 * 1.4, 480 * 1.4))