"""Contains the Main App :class:`AnkiCardGenApp`."""

import os
import queue
from functools import partial

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import DictProperty, ListProperty, ObjectProperty
from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.picker import MDThemePicker

from custom_widgets.main_menu import MainMenu
from generate_anki_card import AnkiObject
from utils import now_string, smart_loader, smart_saver
from words import Word

this_dir = os.path.dirname(__file__)
if this_dir:
    this_dir = this_dir + "/"
Builder.load_file(f"{this_dir}custom_widgets/main_menu.kv")
Builder.load_file(f"{this_dir}custom_widgets/fixes.kv")


class AnkiCardGenApp(MDApp):
    """Main App."""

    # Kivy
    dialog = ObjectProperty()
    """:class:`~kivymd.uix.dialog.MDDialog` Object."""
    file_manager = ObjectProperty()
    """:class:`~kivymd.uix.filemanager.MDFileManager` Object."""
    theme_dialog = ObjectProperty()
    """:class:`~kivymd.uix.picker.MDThemePicker` Object."""
    # Other Objects
    word = ObjectProperty()
    """:class:`pt_word.Word` Object."""
    anki = ObjectProperty()
    """:class:`generate_anki_card.AnkiObject` Object."""
    queue = ObjectProperty()
    """:class:`queue.Queue` Object."""
    # Data
    error_words = ListProperty([])
    """:class:`~kivy.properties.ListProperty` containing all words that could not be processed by Queue."""
    queue_words = ListProperty([])
    """:class:`~kivy.properties.ListProperty` containing all words not yet made into Anki-cards."""
    done_words = ListProperty([])
    """:class:`~kivy.properties.ListProperty` containing all words for which Anki-cards have been generated."""
    loading_state_dict = DictProperty({})
    """:class:`~kivy.properties.DictProperty` containing all words that could not be processed by Queue."""
    word_state_dict = DictProperty({})
    """:class:`~kivy.properties.DictProperty` containing all words that could not be processed by Queue."""
    keys_to_save = ListProperty(
        [
            "queue_words",
            "done_words",
            "error_words",
            "loading_state_dict",
            "anki",
            "word_state_dict",
        ]
    )
    """:class:`~kivy.properties.ListProperty` containing the name of all attributes that should be saved on change."""

    @mainthread
    def show_dialog(
        self,
        message,
        options=None,
        item_callback=None,
        buttons=None,
        close_on_item=False,
    ):
        """
        Show customizable dialog.

        Args:
          message: Message on top.
          options:  List of strings, each representing an option for the user to choose.
          item_callback:  (Default value = None)
          buttons:  (Default value = None)
          close_on_item: If ``True`` dismiss dialog after click on item. (Default = False)
        """

        def on_item_press(item):
            item_callback(item)
            if close_on_item:
                self.dialog.dismiss()

        if buttons is None:
            buttons = [
                MDFlatButton(
                    text="CANCEL",
                    text_color=self.theme_cls.primary_color,
                    on_press=lambda x: self.dialog.dismiss(),
                )
            ]
        items = [
            OneLineIconListItem(text=option, on_press=on_item_press)
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

    def build_config(self, config):  # pylint: disable=no-self-use
        """If no config-file exists, sets the default."""
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
                "queue_words": "../app_data/queue_words.json",
                "done_words": "../app_data/done_words.json",
                "error_words": "../app_data/error_words.json",
                "loading_state_dict": "../app_data/loading_state_dict.json",
                "anki": "../app_data/anki.p",
                "generated": "../app_data/generated_cards.csv",
                "apkg": "../app_data/apkgs/portuguese_vocab.apkg",
                "word_state_dict": "../app_data/word_state_dict.json",
            },
        )
        os.makedirs("../app_data/", exist_ok=True)
        os.makedirs("../app_data/apkgs/", exist_ok=True)

    def build(self):
        """Set up App and return :class:`custom_widgets.MainMenu` as root widget."""
        # Config and Theme
        self.theme_cls = ThemeManager(  # pylint: disable=attribute-defined-outside-init
            **self.config["Theme"]
        )
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
        )
        self.word = Word(data_dir="../app_data/words")
        self.setup_queue()
        # Kivy Objects
        self.file_manager = MDFileManager()
        return MainMenu()

    def setup_queue(self):
        """Set up :attr:`queue` from words in :attr:`queue_words`."""
        self.queue = queue.Queue()
        for word in self.queue_words:
            if self.loading_state_dict[word] in ["loading", "queued"]:
                self.loading_state_dict[word] = "queued"
                self.queue.put(word)

    def save_theme(self, *_):
        """Save current theme to config file."""
        for key in self.config["Theme"]:
            self.config["Theme"][key] = getattr(self.theme_cls, key)
        self.config.write()

    def open_file_manager(self, path="/", select_path=print, ext=None):
        """Open file manager at :attr:`path` and calls :attr:`select_path` with path of selected file."""
        print("opening file manager...")
        if ext is None:
            ext = [".html"]
        self.file_manager.ext = ext
        self.file_manager.select_path = select_path
        self.file_manager.show(path)

    def load_by_config_key(self, key):
        """Use :func:`utils.smart_loader` to load attribute from path in :attr:`config` [attribute]."""
        path = self.config["Paths"][key]
        setattr(self, key, smart_loader(path))

    def save_by_config_key(self, key, *_, obj=None):
        """Use :func:`utils.smart_saver` to save current attribute to path in :attr:`config` [attribute]."""
        if obj is None:
            obj = getattr(self, key)
        path = self.config["Paths"][key]
        smart_saver(obj, path)

    def load_app_state(self):
        """
        Load all attributes specified in :attr:`keys_to_save` by :meth:`load_by_config_key`.

        If the path does not exists (first run of app), sets them up for the next time.
        """
        for key in self.keys_to_save:
            try:
                self.load_by_config_key(key)
            except FileNotFoundError:
                print(f"No existing file for {key}. Created new one.")
                self.save_by_config_key(key)

    def add_anki_card(self, result_dict):
        """Write apkg, json-file of card content."""
        toast(f'Added card for "{result_dict["Word"]}" to Deck.', 10)
        smart_saver(
            result_dict,
            f"../app_data/words/{self.word.folder()}/{self.word.folder()}_card.json",
        )
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
