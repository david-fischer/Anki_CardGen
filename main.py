import os
import queue
from functools import partial

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import DictProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior, ThemeManager
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list import MDList, OneLineIconListItem
from kivymd.uix.picker import MDThemePicker

from anki.generate_anki_card import AnkiObject
from my_kivy.mychooser import CheckBehavior, CheckContainer
from utils import now_string, smart_loader, smart_saver, widget_by_id
from word_requests.pt_word import Word

this_dir = os.path.dirname(__file__)
if this_dir:
    this_dir = this_dir + "/"
Builder.load_file(f"{this_dir}my_kivy/screens.kv")
Builder.load_file(f"{this_dir}my_kivy/fixes.kv")


class DrawerItem(CheckBehavior, OneLineIconListItem):
    icon = StringProperty()
    screen_name = StringProperty("test")

    def __init__(self, **kwargs):
        super(DrawerItem, self).__init__(**kwargs)
        self.theme_cls.bind(theme_style=self.__post_init__)
        self.theme_cls.bind(primary_palette=self.__post_init__)

    def __post_init__(self, *_):
        self.state_dicts = {
            True: {"text_color": self.theme_cls.primary_color},
            False: {"text_color": self.theme_cls.text_color},
        }
        super(DrawerItem, self).__post_init__()

    def on_release(self):
        self.current_state = True
        widget_by_id("nav_drawer").set_state("close")


class DrawerList(ThemableBehavior, CheckContainer, MDList):
    check_one = True
    CheckElementObject = DrawerItem
    current = StringProperty("")

    def conditional_uncheck(self, instance, value):
        super(DrawerList, self).conditional_uncheck(instance, value)
        self.current = instance.screen_name

    def click_screen_name(self, screen_name):
        for item in self.children:
            if item.screen_name == screen_name:
                item.on_release()


class MainMenu(StackLayout):
    screen_dicts = ListProperty(
        [
            {
                "icon": "form-textbox",
                "text": "Manual Input",
                "screen_name": "screen_single_word",
            },
            {
                "icon": "format-list-checkbox",
                "text": "Queue",
                "screen_name": "screen_queue",
            },
            {"icon": "cogs", "text": "Settings", "screen_name": "screen_settings"},
            # {"icon": "folder", "text": "My files", "screen_name": "my_files"},
        ]
    )

    def on_parent(self, *_):
        for screen_dict in self.screen_dicts:
            name = screen_dict["screen_name"]
            path = f"my_kivy/{name}.kv"
            screen = Screen(name=name)
            if not os.path.exists(path):
                with open(path, "w") as file:
                    file.write(f'MDLabel:\n\ttext:"{name}"')
            screen.add_widget(Builder.load_file(path))
            self.ids.screen_man.add_widget(screen)
        self.ids.drawer_list.element_dicts = self.screen_dicts
        self.ids.drawer_list.bind(current=self.ids.screen_man.setter("current"))
        self.ids.drawer_list.children[-1].on_release()


class AnkiCardGenApp(MDApp):
    # Kivy
    dialog = ObjectProperty()
    file_manager = ObjectProperty()
    theme_dialog = ObjectProperty()
    # Other Objects
    word = ObjectProperty()
    anki = ObjectProperty(rebind=True)
    q = ObjectProperty()
    # Data
    error_words = ListProperty([])
    queue_words = ListProperty([])
    loading_state_dict = DictProperty({})
    done_words = ListProperty([])
    keys_to_save = ListProperty(
        ["queue_words", "done_words", "error_words", "loading_state_dict", "anki"]
    )

    @mainthread
    def show_dialog(
        self, message, options=None, callback=print, item_function=None, buttons=None
    ):
        if item_function is None:

            def item_function(obj):
                self.dialog.dismiss()
                callback(obj.text)

        if buttons is None:
            buttons = [
                MDFlatButton(
                    text="CANCEL",
                    text_color=self.theme_cls.primary_color,
                    on_press=lambda x: self.dialog.dismiss(),
                )
            ]
        items = [
            OneLineIconListItem(text=option, on_press=item_function)
            for option in options
        ]
        self.dialog = MDDialog(
            title=message,
            type="simple",
            items=items,
            auto_dismiss=False,
            buttons=buttons,
        )
        self.dialog.ids.title.color = self.dialog.theme_cls.text_color
        self.dialog.open()

    def build_config(self, config):
        config.setdefaults(
            "Theme",
            {
                "primary_palette": "Red",
                "accent_palette": "Amber",
                "theme_style": "Dark",
            },
        )
        config.setdefaults(
            "Paths",
            {
                "queue_words": "app_state/queue_words.json",
                "done_words": "app_state/done_words.json",
                "error_words": "app_state/error_words.json",
                "loading_state_dict": "app_state/loading_state_dict.json",
                "anki": "app_state/anki.p",
                "generated": "app_state/generated_cards.csv",
                "apkg": "apkgs/portuguese_vocab.apkg",
            },
        )
        os.makedirs("app_state", exist_ok=True)

    def build(self):
        # Config and Theme
        self.theme_cls = ThemeManager(**self.config["Theme"])
        self.theme_dialog = MDThemePicker()
        self.theme_dialog.ids.close_button.bind(on_press=self.save_theme)
        # Non Kivy Objects
        # The following condition is a workaround:
        # If we set self.anki = AnkiObject(...) and load from the pickled file
        # afterwards, the object is not loaded correctly and we start with an empty deck...
        if not os.path.exists(self.config["Paths"]["anki"]):
            self.anki = AnkiObject(root_dir="anki")
        self.load_app_state()
        self.bind(
            **{
                key: partial(self.save_by_config_key, key, obj=None)
                for key in self.keys_to_save
            }
        )  # partial(
        self.word = Word()
        self.setup_queue()
        # Kivy Objects
        self.file_manager = MDFileManager()
        return Builder.load_string("MainMenu:")

    # def on_start(self):
    #    threading.Thread(target=make_screenshots).start()

    def setup_queue(self):
        self.q = queue.Queue()
        for word in self.queue_words:
            if self.loading_state_dict[word] in ["loading", "queued"]:
                self.loading_state_dict[word] = "queued"
                self.q.put(word)

    def save_theme(self, *_):
        for key in self.config["Theme"]:
            self.config["Theme"][key] = getattr(self.theme_cls, key)
        self.config.write()

    def open_file_manager(self, path="/", select_path=print, ext=None):
        print("opening file manager...")
        if ext is None:
            ext = [".html"]
        self.file_manager.ext = ext
        self.file_manager.select_path = select_path
        self.file_manager.show(path)

    def load_by_config_key(self, key):
        path = self.config["Paths"][key]
        setattr(self, key, smart_loader(path))

    def save_by_config_key(self, key, *_, obj=None):
        if obj is None:
            obj = getattr(self, key)
        path = self.config["Paths"][key]
        smart_saver(obj, path)

    def load_app_state(self):
        for key in self.keys_to_save:
            try:
                self.load_by_config_key(key)
            except FileNotFoundError:
                print(f"No existing file for {key}. Created new one.")
                self.save_by_config_key(key)

    def add_anki_card(self, result_dict):
        toast(f'Added card for "{result_dict["Word"]}" to Deck.', 10)
        smart_saver(result_dict, f"{self.word.folder()}/{self.word.folder()}.json")
        self.save_by_config_key("generated", obj=result_dict)
        self.anki.add_card(**result_dict)
        apkg_path = self.config["Paths"]["apkg"]
        apkg_bkp_path = f"{apkg_path[:-5]}_{now_string()}.apkg"
        self.anki.write_apkg(apkg_path)
        self.anki.write_apkg(apkg_bkp_path)
        self.save_by_config_key("anki")
        self.done_words.append(result_dict["Word"])


if __name__ == "__main__":
    AnkiCardGenApp().run()
