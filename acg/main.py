"""Contains the Main App :class:`AnkiCardGenApp`."""
__version__ = "1.0.7"

import os
import pydoc

import certifi
from kivy import platform
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ConfigParserProperty,
    DictProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.modalview import ModalView
from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivymd.uix.spinner import MDSpinner
from pony.orm import db_session

from custom_widgets.main_menu import MainMenu
from db import add_missing_templates, get_template
from paths import ANKI_DIR, CUSTOM_WIDGET_DIR
from utils import smart_loader, smart_saver

os.environ["SSL_CERT_FILE"] = certifi.where()


Builder.load_file(os.path.join(CUSTOM_WIDGET_DIR, "main_menu.kv"))
Builder.load_file(os.path.join(CUSTOM_WIDGET_DIR, "fixes.kv"))


class AnkiCardGenApp(MDApp):
    """Main App."""

    # Data
    word_state_dict = DictProperty({})
    """:class:`~kivy.properties.DictProperty` containing all words that could not be processed by Queue."""
    current_template_name = StringProperty("Portuguese Vocab")
    template = ObjectProperty()
    apkg_export_dir = ConfigParserProperty("apgks", "Paths", "apkg_export_dir", "app")
    anki_template_dir = ConfigParserProperty(
        "vocab_card", "Paths", "anki_template_dir", "app"
    )
    busy = BooleanProperty(False)
    busy_modal = ObjectProperty(None)  #

    def get_anki_template_dir(self):
        """Return absolute path where html-, css- and js-files for anki-card is located."""
        return os.path.join(ANKI_DIR, self.anki_template_dir)

    def build_config(self, config):  # pylint: disable=no-self-use
        """If no config-file exists, sets the default."""
        config.setdefaults(
            "Theme",
            {
                "primary_palette": "Red",
                "accent_palette": "Amber",
                "theme_style": "Light",
            },
        )
        config.setdefaults(
            "Paths", {"anki_template_dir": "vocab_card", "apkg_export_dir": "apkgs"},
        )
        # os.makedirs("../app_data/", exist_ok=True)
        # os.makedirs("../app_data/apkgs/", exist_ok=True)

    def build(self):
        """Set up App and return :class:`custom_widgets.MainMenu` as root widget."""
        # Config and Theme
        add_missing_templates()
        self.theme_cls = ThemeManager(  # pylint: disable=attribute-defined-outside-init
            **self.config["Theme"]
        )
        self.word_state_dict = self.get_word_states()
        print(self.word_state_dict)
        return MainMenu()

    def save_theme(self, *_):
        """Save current theme to config file."""
        for key in self.config["Theme"]:
            self.config["Theme"][key] = getattr(self.theme_cls, key)
        self.config.write()

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

    def on_current_template_name(self, *_):
        """Set up new template if :attr:`current_template_name` changes."""
        self.setup_template()

    def on_start(self):
        """Set up template on start of app."""
        super(AnkiCardGenApp, self).on_start()
        self.setup_template()
        print(vars(self.config))

    def get_word_states(self):
        """Return dict of word-states for current template from data-base."""
        with db_session:
            return {
                card.name: card.state for card in self.get_current_template_db().cards
            }

    @mainthread
    def on_busy(self, *_):
        """Set up :attr:`busy_modal` if necessary. Then open or close it depending on state of :attr:`busy`."""
        if not self.busy_modal:
            self.busy_modal = ModalView(
                auto_dismiss=False, size_hint=(1.2, 1.2), opacity=0.5,
            )
            spinner = MDSpinner(active=False, size_hint=(0.5, 0.5))
            self.busy_modal.add_widget(spinner)
            self.bind(busy=spinner.setter("active"))
        if self.busy:
            self.busy_modal.open()
        else:
            self.busy_modal.dismiss()


def main():
    """Main-function."""
    if platform == "android":
        from android.permissions import (  # pylint: disable=import-outside-toplevel
            request_permissions,
            Permission,
        )

        request_permissions(
            [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
        )
    AnkiCardGenApp().run()


if __name__ == "__main__":
    main()
