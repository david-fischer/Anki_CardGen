"""Contains the Main App :class:`AnkiCardGenApp`."""
__version__ = "1.0.7"

import os
import pydoc

import certifi
from kivy import platform
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    ConfigParserProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.modalview import ModalView
from kivymd.app import MDApp
from kivymd.uix.spinner import MDSpinner
from pony.orm import db_session

from custom_widgets.main_menu import MainMenu
from db import add_missing_templates, get_template
from paths import ANKI_DIR, CUSTOM_WIDGET_DIR

os.environ["SSL_CERT_FILE"] = certifi.where()

Builder.load_file(os.path.join(CUSTOM_WIDGET_DIR, "main_menu.kv"))
Builder.load_file(os.path.join(CUSTOM_WIDGET_DIR, "fixes.kv"))


class AnkiCardGenApp(MDApp):
    """Main App."""

    # Data
    current_template_name = StringProperty("Portuguese Vocab")
    template = ObjectProperty()
    # CONFIG
    apkg_export_dir = ConfigParserProperty("", "Paths", "apkg_export_dir", "app")
    anki_template_dir = ConfigParserProperty(
        "vocab_card", "Paths", "anki_template_dir", "app"
    )
    primary_palette = ConfigParserProperty("Red", "Theme", "primary_palette", "app")
    accent_palette = ConfigParserProperty("Amber", "Theme", "accent_palette", "app")
    theme_style = ConfigParserProperty("Light", "Theme", "theme_style", "app")

    busy = BooleanProperty(False)
    busy_modal = ObjectProperty(None)  #

    def get_anki_template_dir(self):
        """Return absolute path where html-, css- and js-files for anki-card is located."""
        return os.path.join(ANKI_DIR, self.anki_template_dir)

    def build_config(self, config):  # pylint: disable=no-self-use
        """If no config-file exists, sets the default."""
        config.setdefaults("Theme", {})
        config.setdefaults("Paths", {})

    def bind_theme_cls_and_config(self):
        """Bind :attr:`theme_cls` and the corresponding :class:`~kivy.properties.ConfigParserProperties`."""
        keys = self.config["Theme"]
        self.bind(**{key: self.theme_cls.setter(key) for key in keys})
        self.theme_cls.bind(**{key: self.setter(key) for key in keys})
        for key in keys:
            setattr(self.theme_cls, key, getattr(self, key))

    def build(self):
        """Set up App and return :class:`custom_widgets.MainMenu` as root widget."""
        add_missing_templates()
        self.bind_theme_cls_and_config()
        if not self.apkg_export_dir:
            self.apkg_export_dir = self.user_data_dir
        return MainMenu()

    def get_current_template_db(self):
        """Return data-base object for :attr:`current_template_name`."""
        return get_template(self.current_template_name)

    def get_word_states(self):
        """Return dict of word-states for current template from data-base."""
        with db_session:
            return {
                card.name: card.state for card in self.get_current_template_db().cards
            }

    word_state_dict = AliasProperty(
        getter=get_word_states, setter=None, bind=["current_template_name"]
    )

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
