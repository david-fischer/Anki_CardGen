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
MEANING2COLOR = {val: key for key, val in COLOR2MEANING.items()}

nlp = None


# GENERAL


class CD:
    """Context manager for changing the current working directory"""

    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)
        self.saved_path = None

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


def save_dict_to_csv(some_dict, out_path):
    is_first_entry = not os.path.exists(out_path)
    with open(out_path, "a") as file:
        writer = csv.DictWriter(file, fieldnames=some_dict.keys())
        if is_first_entry:
            writer.writeheader()
        writer.writerow(some_dict)


def load_dicts_from_csv(path):
    with open(path, "r") as read_obj:
        return list(csv.DictReader(read_obj))


def smart_loader(path):
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


def sleep_decorator(time):
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


def make_screenshots(window_size=[270 * 1.4, 480 * 1.4]):
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


# TODO: path remove ..
def save_card_htmls(word="casa"):
    with CD("../screenshots"):
        field_dict = smart_loader(f"../app_data/words/{word}/{word}_card.json")
        field_dict["Audio"] = "&#9658;"
        shutil.copytree("anki/", word)
        with CD(word):
            shutil.copy(f"../../data/{word}/{word}.jpg", "..")
            paths = glob("*.html")
            for path in paths:
                print()
                with open(path, "r") as file:
                    html_template = file.read()
                with open(path, "w") as file:
                    file.write(rend.render(html_template, field_dict))


def save_card_pngs(word="casa", size=(540, 960)):
    # with CD(f"screenshots/{word}"):
    paths = glob("anki/*.html")
    field_dict = smart_loader(f"../app_data/words/{word}/{word}_card.json")
    field_dict["Audio"] = "&#9658;"
    try:
        shutil.copytree("anki/js", "/tmp/js/")
        shutil.copytree("anki/css", "/tmp/css/")
    except:
        print("JS AND CSS FOLDER ALREADY EXIST IN /tmp/ skip copying.")
    shutil.copy2(f"../app_data/words/{word}/{word}.jpg", f"/tmp/{word}.jpg")
    compress_img(f"/tmp/{word}.jpg", width=int(size[0]) - 12)
    os.makedirs(f"screenshots/{word}", exist_ok=True)
    for path in paths:
        with open(path, "r") as file:
            string = file.read()
            string = rend.render(string, **field_dict)
        imgkit.from_string(
            string,
            f'screenshots/{word}/{os.path.basename(path).replace(".html",".png")}',
            options={
                "width": int(size[0]),
                "height": int(size[1]),
                "allow": "./anki/*",
                # "--allow": f"../../words/{word}"
            },
        )


def selection_helper(base, id=None, props=None):
    if props is None:
        props = ["text"]
    base_obj = getattr(base.ids, id) if id is not None else base
    out = [base_obj.get_checked(property_name=prop) for prop in props]
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
        words = [word.strip(",.;:-–—!?¿¡\"'") for word in words]
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


def word_list_from_txt(path):
    with open(path, "r") as file:
        words = file.read().splitlines()
    return words


def tag_word_in_sentence(sentence, tag_word):
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
