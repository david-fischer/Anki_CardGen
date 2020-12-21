"""Contains the Main App :class:`AnkiCardGenApp`."""
__version__ = "1.0.11"

import os
import pydoc

import certifi
import screens
import toolz
from custom_widgets.main_menu import MainMenu
from db import add_missing_templates, get_template
from kivy import platform
from kivy.clock import mainthread
from kivy.properties import (
    BooleanProperty,
    ConfigParserProperty,
    DictProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.modalview import ModalView
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.spinner import MDSpinner
from paths import ANKI_DIR, ROOT_DATA_DIR
from pony.orm import db_session

os.environ["SSL_CERT_FILE"] = certifi.where()


class AnkiCardGenApp(MDApp):
    """Main App."""

    # Data
    current_template_name = StringProperty("Portuguese Vocab")
    template = ObjectProperty()

    # Config
    apkg_export_dir = ConfigParserProperty(
        "",
        "Paths",
        "apkg_export_dir",
        "app",
    )
    import_dir = ConfigParserProperty("", "Paths", "import_dir", "app")
    kobo_import_dir = ConfigParserProperty("", "Paths", "kobo_import_dir", "app")
    anki_template_dir = ConfigParserProperty(
        "vocab_card", "Paths", "anki_template_dir", "app"
    )
    primary_palette = ConfigParserProperty("Red", "Theme", "primary_palette", "app")
    accent_palette = ConfigParserProperty("Amber", "Theme", "accent_palette", "app")
    theme_style = ConfigParserProperty("Light", "Theme", "theme_style", "app")
    source_language = ConfigParserProperty("en", "Languages", "source_language", "app")
    target_language = ConfigParserProperty("pt", "Languages", "target_language", "app")

    busy = BooleanProperty(False)
    busy_modal = ObjectProperty(None)

    file_manager = ObjectProperty(None)

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
        self.word_state_dict = self.get_word_states()
        self.bind_theme_cls_and_config()
        self.file_manager = MDFileManager()
        self.apkg_export_dir = self.apkg_export_dir or os.path.join(
            ROOT_DATA_DIR, "ankicardgen"
        )
        self.import_dir = self.import_dir or os.path.abspath(ROOT_DATA_DIR)
        os.makedirs(self.apkg_export_dir, exist_ok=True)
        return MainMenu(screen_dicts=screens.screen_dicts)

    def get_current_template_db(self):
        """Return data-base object for :attr:`current_template_name`."""
        return get_template(self.current_template_name)

    def get_word_states(self):
        """Return dict of word-states for current template from data-base."""
        with db_session:
            return {
                card.name: card.state for card in self.get_current_template_db().cards
            }

    word_state_dict = DictProperty()  # AliasProperty(

    # getter=get_word_states, setter=None, bind=["current_template_name"]
    # )

    def new_template_instance(self):
        """Return new instance of current template class."""
        template_cls_name = self.get_current_template_db().cls_name
        template_cls = pydoc.locate(template_cls_name)
        return template_cls()

    def init_template(self):
        """Set :attr:`template` to new instance of class corresponding to :attr:`current_template_name`."""
        self.template = self.new_template_instance()

    def on_current_template_name(self, *_):
        """Set up new template if :attr:`current_template_name` changes."""
        self.init_template()

    def on_start(self):
        """Set up template on start of app."""
        super().on_start()
        self.init_template()
        self.request_permissions()

    def on_pause(self):  # pylint: disable=no-self-use
        """Enable coming back to app."""
        return True

    @mainthread
    def on_busy(self, *_):
        """Set up :attr:`busy_modal` if necessary. Then open or close it depending on state of :attr:`busy`."""
        if not self.busy_modal:
            self.busy_modal = ModalView(
                auto_dismiss=False,
                size_hint=(1.2, 1.2),
                opacity=0.5,
            )
            spinner = MDSpinner(active=False, size_hint=(0.5, 0.5))
            self.busy_modal.add_widget(spinner)
            self.bind(busy=spinner.setter("active"))
        if self.busy:
            self.busy_modal.open()
        else:
            self.busy_modal.dismiss()

    def open_file_manager(self, path=".", callback=print, ext=None, close_after=True):
        """Open file manager at :attr:`path` and calls :attr:`select_path` with path of selected file."""
        if close_after:
            callback = toolz.functoolz.juxt(
                callback, lambda *_: self.file_manager.close()
            )
        path = os.path.abspath(path)
        ext = ext or ["*"]
        self.file_manager.ext = ext
        self.file_manager.select_path = callback
        self.file_manager.show(path)

    @staticmethod
    def request_permissions():
        """Request storage permissions on android."""
        if platform == "android":
            from android.permissions import (  # pylint: disable=import-outside-toplevel
                Permission,
                request_permissions,
            )

            request_permissions(
                [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
            )


def main():
    """Main-function."""
    AnkiCardGenApp().run()


if __name__ == "__main__":
    main()
