"""Contains the Main App :class:`AnkiCardGenApp`."""

import os
import pydoc

from kivy.lang import Builder
from kivy.properties import DictProperty, ObjectProperty, StringProperty
from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.picker import MDThemePicker
from pony.orm import db_session

from custom_widgets.main_menu import MainMenu
from db import get_template
from generate_anki_card import AnkiObject
from utils import smart_loader, smart_saver, widget_by_id
from words import Word

this_dir = os.path.dirname(__file__)
if this_dir:
    this_dir += "/"
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
    # Data
    word_state_dict = DictProperty({})
    """:class:`~kivy.properties.DictProperty` containing all words that could not be processed by Queue."""
    current_template_name = StringProperty("Portuguese Vocab")
    template = ObjectProperty()
    apkg_export_dir = StringProperty("../app_data/apkgs")

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
            "Paths", {"word_state_dict": "../app_data/word_state_dict.json",},
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
        self.word_state_dict = self.get_word_states()
        print(self.word_state_dict)
        self.word = Word(data_dir="../app_data/words")
        # Kivy Objects
        self.file_manager = MDFileManager()
        return MainMenu()

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

    def get_current_template_db(self):
        """Return data-base object for :attr:`current_template_name`."""
        return get_template(self.current_template_name)

    def setup_template(self):
        """Initialize :class:`templates.Template` and adds it to the single_word screen."""
        template_cls_name = self.get_current_template_db().cls_name
        template_cls = pydoc.locate(template_cls_name)
        self.template = template_cls()
        template_parent = widget_by_id("single_word/scroll_view")
        if template_parent.children:
            template_parent.clear_widgets()
        template_parent.add_widget(self.template)

    def on_current_template_name(self, *_):
        """Set up new template if :attr:`current_template_name` changes."""
        self.setup_template()

    def on_start(self):
        """Set up template on start of app."""
        super(AnkiCardGenApp, self).on_start()
        self.setup_template()

    def get_word_states(self):
        """Return dict of word-states for current template from data-base."""
        with db_session:
            return {
                card.name: card.state for card in self.get_current_template_db().cards
            }


if __name__ == "__main__":
    AnkiCardGenApp().run()
