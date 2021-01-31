"""This module contains lots of helper functions."""
import asyncio
import csv
import inspect
import json
import os
import pickle
import pwd
import re
import threading
from contextlib import ContextDecorator, contextmanager
from datetime import datetime
from functools import partial, wraps
from io import BytesIO
from itertools import chain, tee
from timeit import default_timer
from typing import Any, Callable

import toolz
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.filemanager import MDFileManager
from PIL import Image
from pony.orm import db_session

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
    with open(path) as read_obj:
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
    with open(path) as file:
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


def split_on_condition(seq, condition):
    """Return two lazy generators for ``True`` and ``False`` respectively."""
    condition_true, condition_false = tee((condition(item), item) for item in seq)
    return (i for p, i in condition_true if p), (i for p, i in condition_false if not p)


def pop_unchanged(dictionary):
    """Pop all values from dict where key=val."""
    return [dictionary.pop(key) for key in list(dictionary) if dictionary[key] == key]


# Image resizing
def compress_img_bytes(bytes_image, width=512):
    """Compress image given as bytes (e.g. as content of :class:`requests.Response`)."""
    img = Image.open(BytesIO(bytes_image))
    if img.size[0] > width:
        resize = (width, width * img.size[1] // img.size[0])
        img = img.resize(resize, Image.ANTIALIAS)
    output = BytesIO()
    img.save(
        output,
        format="JPEG",
        optimize=True,
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


def update_word_state_dict(word, state):
    """Set state in app.word_state_dict."""
    MDApp.get_running_app().word_state_dict[word] = state


@db_session
def set_word_state(word, state):
    """Set state in the data-base entry of the card of the current template."""
    MDApp.get_running_app().get_current_template_db().get_card(word).state = state


def not_implemented_toast(*_):
    """Display toast notifying user that the function is not implemented."""
    toast("Not implemented yet.")


def get_username():
    """Return name of currently active user."""
    return pwd.getpwuid(os.getuid())[0]


def is_duplicate(word):
    """Check if word is already present in the app.word_state_dict."""
    return word in MDApp.get_running_app().word_state_dict


@contextmanager
def get_file_manager(ext=None, callback=None):
    """Get file manager.

    Context manager to temporarily set `ext` and `callback` of file_manager.
    """
    app = MDApp.get_running_app()
    if getattr(app, "file_manager") is None:
        app.file_manager = MDFileManager()
    file_manager = app.file_manager
    try:
        file_manager.close()
    except AttributeError:
        pass
    file_manager.ext, ext = ext, app.file_manager.ext
    file_manager.select_path = partial(
        close_and_callback,
        file_manager=file_manager,
        callback=callback,
        old_callback=file_manager.select_path,
    )
    try:
        yield file_manager
    finally:
        file_manager.ext, ext = ext, app.file_manager.ext


def close_and_callback(file_path, file_manager=None, callback=None, old_callback=None):
    """Helper-function for :func:`get_file_manager`."""
    file_manager.close()
    callback(file_path)
    if old_callback:
        file_manager.select_path = old_callback


def contains_newline(match):
    r"""Return '\n' or " "."""
    return "\n" if "\n" in match[0] else " "


def remove_whitespace(some_string):
    """Replace each group of whitespaces by a simple space (or by a newline if at least one is in the match)."""
    return re.sub(r"\s+", contains_newline, some_string).strip()


@contextmanager
def timer(process):
    """Print execution time."""
    start = default_timer()
    yield lambda: print(default_timer() - start)
    print(f"{process} took {default_timer() - start}s.")


async def async_wrapper(functions, *args):
    """Gather async functions."""
    return await asyncio.gather(*[a(*args) for a in functions])


def async_get_results(functions: Callable[[Any], dict], *args):
    """Get merged dict from gathered async-run."""
    return smart_dict_merge(asyncio.run(async_wrapper(functions, *args)))
