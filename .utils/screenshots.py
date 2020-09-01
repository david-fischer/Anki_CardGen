"""Script to automatically take screenshots of the app in given states."""
import os
import re
import shutil
import sys
import threading
from functools import partial
from glob import glob
from time import sleep

import fire
import imgkit
import pystache
import toolz
from kivy.clock import Clock, mainthread
from kivy.core.image import Image as KivyImage
from kivy.core.window import Window
from kivy.graphics.context_instructions import Scale, Translate
from kivy.graphics.fbo import Fbo
from kivy.graphics.gl_instructions import ClearBuffers, ClearColor
from kivy.input.recorder import Recorder
from kivymd.app import MDApp
from kivymd.toast import toast

sys.path.append(os.path.abspath("acg"))
print(sys.path)


from utils import (  # pylint: disable=wrong-import-position
    CD,
    compress_img,
    set_screen,
    smart_loader,
    widget_by_id,
)

rend = pystache.Renderer(escape=lambda s: s)


def sleep_decorator(time):
    """Execute sleep(time) before and after decorated function."""

    def the_real_decorator(function):
        def wrapper(*args, **kwargs):
            sleep(time)
            function(*args, **kwargs)
            sleep(time)

        return wrapper

    return the_real_decorator


@mainthread
def screenshot(path, root_widget=None):
    """
    Take screenshot of the current state of the app and save it under ``path``.

    The sleep- and mainthread-decorator ensure that the app shows the current state properly.
    """
    if root_widget is None:
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


def make_screenshots(*_, window_size=(270 * 1.4, 480 * 1.4)):
    """Set the app in a number of predefined states and takes a screenshot of each."""
    Window.size = window_size
    widget_by_id("nav_drawer").set_state("open")
    screenshot("../screenshots/0-nav_drawer_open.png")
    widget_by_id("nav_drawer").set_state("close")
    for screen_name in widget_by_id("/").get_screen_names():
        set_screen(screen_name)
        screenshot(f"../screenshots/{screen_name}.png")
    set_screen("single_word")
    single_word_root = widget_by_id("single_word")
    single_word_root.template.search("casa")
    image_carousel = single_word_root.template.fields[2].widget
    sleep(1)
    screenshot("../screenshots/1-word_1.png")
    image_carousel.open_menu()
    sleep(1)
    screenshot("../screenshots/3-word_images.png", root_widget=image_carousel.modal)
    image_carousel.modal.dismiss()
    single_word_root.scroll_view.scroll_y = 0.1
    screenshot("../screenshots/2-word_2.png")
    # Queue
    set_screen("queue")
    widget_by_id("queue/speed_dial/").open_stack(1)
    screenshot("../screenshots/4-import.png")
    set_screen("history")
    widget_by_id("history/speed_dial/").open_stack(1)
    screenshot("../screenshots/5-export.png")
    os._exit(0)  # pylint: disable=protected-access


def save_card_pngs(word="casa", size=(540, 960)):
    """
    Save pngs of the anki-cards for a given word.

    The fields need to be saved as json at ``../app_data/<word>/<word>_card.json``.

    Args:
      word:  (Default value = "casa")
      size:  (Default value = (540,960))
    """
    paths = glob("anki/*.html")
    field_dict = smart_loader(f"../app_data/words/{word}/{word}_card.json")
    field_dict["Audio"] = "&#9658;"
    try:
        shutil.copytree("../acg/anki/js", "/tmp/js/")
        shutil.copytree("../acg/anki/css", "/tmp/css/")
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
            f'../screenshots/{word}/{os.path.basename(path).replace(".html", ".png")}',
            options={"width": int(size[0]), "height": int(size[1]),},
        )


def start_thread(func):
    """Start a thread."""
    thread = threading.Thread(target=func)
    thread.start()


def stop_recording(_instance, key, *_, recorder=None):
    if key == 289:
        # toast("Start" if not recorder.record else "Stop")
        recorder.record = not recorder.record


@mainthread
def main_thread_screenshot(name, window_size=(405, 720)):
    # Window.size = window_size
    Clock.schedule_once(lambda t: Window.screenshot(name=name))


def make_recordings():
    names = [
        "0-nav-drawer-open",
        "1-word-0",
        "2-word-1",
        "3-word-images",
        "4-import",
        "5-export",
    ]
    toast(f"Screenshot with F8.")
    for i, name in enumerate(names):
        print(i, name)
        rec = Recorder(filename=f"recordings/{name}.kvi")
        stop_rec = partial(stop_recording, recorder=rec)
        Window.bind(on_keyboard=stop_rec)
        rec.record = True
        while rec.record:
            sleep(0.5)
        Window.unbind(on_keyboard=stop_rec)
        main_thread_screenshot(f"../screenshots/{name}.png")
    rename_screenshots()
    sleep(2)
    os._exit(0)


def play_recordings(folder):
    print(folder)
    rec_files = sorted(glob(f"{folder}/*.kvi"))
    for rec_file in rec_files:
        print(rec_file)
        rec = Recorder(filename=rec_file)
        rec.play = True
        name = re.split(r"[/.]", rec_file)[-2]
        print(name)
        while rec.play:
            sleep(0.5)
        main_thread_screenshot(name=f"../screenshots/{name}.png")
    sleep(2)
    rename_screenshots()
    os._exit(0)


def rename_screenshots():
    for old in glob("../screenshots/*.png"):
        new = re.sub(r"\d{4}", "", old)
        os.rename(old, new)


def main(command_fn):

    with CD("acg"):
        from main import AnkiCardGenApp

        app = AnkiCardGenApp()
        app.on_start = toolz.juxt(app.on_start, command_fn)
        app.run()


def play():
    play_fn = partial(start_thread, partial(play_recordings, "../.utils/recordings/"))
    main(play_fn)


def record():
    record_fn = partial(start_thread, make_recordings)
    main(record_fn)


if __name__ == "__main__":
    fire.Fire(
        {"play": play, "record": record,}
    )
