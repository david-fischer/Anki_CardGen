"""This module contains lots of helper functions."""

import csv
import inspect
import json
import os
import pickle
import re
import threading
from collections import defaultdict
from contextlib import ContextDecorator
from datetime import datetime
from functools import partial, wraps
from io import BytesIO
from itertools import chain

import toolz
from bs4 import BeautifulSoup
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
    """Save dictionary as row to csv."""
    is_first_entry = not os.path.exists(out_path)
    with open(out_path, "a") as file:
        writer = csv.DictWriter(file, fieldnames=some_dict.keys())
        if is_first_entry:
            writer.writeheader()
        writer.writerow(some_dict)


def load_dicts_from_csv(path):
    """
    Load csv. Has to have the keys as first line.

    Returns:
        : List of dictionaries.
    """
    with open(path, "r") as read_obj:
        return list(csv.DictReader(read_obj))


def smart_loader(path):
    """
    Use file ending of path to determine which function to use to load file.

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
    Use file ending of path to determine which function to use to save file.

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


def merge_or_last(args):
    """If all args are list, returns merged list. Else returns last arg."""
    if all(isinstance(a, list) for a in args) and len(args) > 1:
        return list(chain(*args))
    return args[-1]


def smart_dict_merge(*args):
    """If values are lists they are merged, else the last element is chosen as new value."""
    return toolz.merge_with(merge_or_last, *args)


def now_string():
    """Return current time in the format ``YYYY-MM-DD_HH:MM:SS``."""
    return str(datetime.now()).split(".")[0].replace(" ", "_")


# KIVY


def set_screen(screen_name):
    """Set current screen to the one with name ``screen_name``."""
    MDApp.get_running_app().root.set_screen(None, screen_name)


def widget_by_id(string):
    """
    Get widget by string of ids, separated by "/".

    Args:
      string: Strings of ids, separated by "/". The first one can be a screen name.

    Returns:
      : widget

    Examples
      >>> print(widget_by_id("single_word/word_prop").__name__)
      MDApp.get_running_app().root.get_screen("single_word").children[
      0].ids.word_prop
    """
    id_list = string.split("/")
    id_list = [id_str for id_str in id_list if id_str != ""]
    obj = MDApp.get_running_app().root
    if id_list:
        first_id = id_list.pop(0)
        if first_id in obj.get_screen_names():
            obj = obj.get_screen(first_id).children[0]
        else:
            obj = getattr(obj.ids, first_id)
        for id_str in id_list:
            obj = getattr(obj.ids, id_str)
    return obj


# KINDLE EXPORT PARSING


def dict_from_kindle_export(file_path):
    """
    Extract highlighted parts and sorts them by color in a dictionary.

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
            words = [" ".join([lemma.lemma_ for lemma in nlp(word)]) for word in words]
            print(words)
        else:
            print("Lemmatization skipped. Spacy module is not installed.")
    return words


def word_list_from_kindle(path):
    """
    Use :const:`MEANING2COLOR` `["words"]` to extract the list of words highlighted in this specific color.

    Args:
      path: Path to html-file exported by kindle.

    Returns:
      : List of highlighted words.
    """
    color = MEANING2COLOR["words"]
    return dict_from_kindle_export(path)[color]


def word_list_from_txt(path):
    """
    Return list of words read as lines from txt-file.

    Args:
      path: Path to txt-file. Each line should correspond to a word (or phrase).
    """
    with open(path, "r") as file:
        words = file.read().splitlines()
    return words


def tag_word_in_sentence(sentence, tag_word):
    """
    Use regex to wrap every derived form of a given ``tag_word`` in ``sentence`` in an html-tag.

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
def compress_img_bytes(bytes_image, width=512):
    """Compress image given as bytes (e.g. as content of :class:`requests.Response`)."""
    img = Image.open(BytesIO(bytes_image))
    if img.size[0] > width:
        resize = (width, width * img.size[1] // img.size[0])
        img = img.resize(resize, Image.ANTIALIAS)
    output = BytesIO()
    img.save(
        output, format="JPEG", optimize=True,
    )
    return output.getvalue()


def compress_img(path, width=512):
    """
    Use the :class:`~PIL.Image` class to reduce the resolution of an image at ``path`` and overwrites it.

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


def pick_val(whitelist, dictionary):
    """Return filtered dictionary, whose values are in ``whitelist``."""
    return toolz.valfilter(lambda k: k in whitelist, dictionary)


# Threading


def start_workers(worker_fn, num):
    """Start a number of ``num`` workers in separate threads.

    Args:
      worker_fn: Function to be started
      num: Number of threads/workers

    """
    workers = [threading.Thread(target=worker_fn, name="worker") for _ in range(num)]
    for worker in workers:
        worker.start()


@toolz.curry
def start_thread(func, fn_arg, **kwargs):
    """
    Wrapper-function to call ``func`` in new thread.

    Every kwarg that fits the signature of ``func`` is plugged into ``func``, the others are used in the constructor of
    :class:`threading.Thread`.

    Note:
        The :meth:`toolz.curry` decorator enables partial evaluation without extra use of partial.

    Examples:
        >>> def f(x,y="y",z="z"):
        ...     print("Hello from",threading.current_thread().name)
        ...     print(x,y,z)
        >>> callback = start_thread(f,z="non_default_z",name="print_thread")
        >>> callback(2)
        Hello from print_thread
        2 y non_default_z
    """
    sig = inspect.signature(func)
    fn_parameters = sig.parameters
    fn_kwargs = toolz.keyfilter(lambda k: k in fn_parameters, kwargs)
    thread_kwargs = toolz.keyfilter(lambda k: k not in fn_parameters, kwargs)
    thread = threading.Thread(
        target=partial(func, fn_arg, **fn_kwargs), **thread_kwargs
    )
    thread.start()


if __name__ == "__main__":
    pass
    #
    # doctest.run_docstring_examples(start_thread)
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
    # save_card_pngs("comecar", size=(270 * 1.4, 480 * 1.4))

    #
    # done, error, words, queue = [
    #     smart_loader(path) for path in sorted(glob("../app_data/*.json"))
    # ]
    # all_words = set(done + error + queue + list(words.keys()))
    # word_dict = {
    #     word: "done"
    #     if word in done
    #     else "error"
    #     if word in error
    #     else "ready"
    #     if word in queue
    #     else None
    #     for word in all_words
    # }
    # word_dict["cachorro"] = "queued"
    # smart_saver(word_dict, "../app_data/word_state_dict.json")


def run_in_thread(func):
    """Call ``func`` in new thread."""

    @wraps(func)
    def run(*k, **kw):
        new_thread = threading.Thread(target=func, args=k, kwargs=kw)
        new_thread.start()
        return new_thread

    return run


class AppBusyContext(ContextDecorator):
    """Set app.busy to ``True`` and back to its previous value."""

    previous_state = None

    def __enter__(self):
        self.previous_state = MDApp.get_running_app().busy
        MDApp.get_running_app().busy = True
        return self

    def __exit__(self, *exc):
        MDApp.get_running_app().busy = self.previous_state
        return False


def app_busy(func):
    """Call function in new thread and set app.busy = ``True`` in the meantime."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return run_in_thread(AppBusyContext()(func))(*args, **kwargs)

    return wrapper
