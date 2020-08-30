"""Implements :class:`SettingsRoot`, the root widget for the settings screen."""
import os
from time import sleep

from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.picker import MDThemePicker
from kivymd.uix.snackbar import Snackbar

from utils import app_busy


class SettingsRoot(BoxLayout):
    """Root widget of the settings screen."""

    theme_dialog = ObjectProperty()
    snackbar = ObjectProperty()

    def __init__(self, **kwargs):
        super(SettingsRoot, self).__init__(**kwargs)
        self.theme_dialog = MDThemePicker()
        self.snackbar = Snackbar()

    @staticmethod
    @app_busy
    def sleep_some():
        """Test-function."""
        sleep(5)

    def check_dir(self, directory):
        """
        Check if ``directory`` exists, offer user choice to create it if not.

        Then, set apkg_export_dir in app and the text-field accordingly.
        """
        print(directory)
        if os.path.exists(directory):
            self.set_export_dir(directory)
            return
        base = os.path.dirname(directory)
        if os.path.exists(base):
            self.snackbar = Snackbar(
                text=f"{directory}   does not exists. Create?",
                button_text="CREATE",
                button_callback=lambda *_: self.set_export_dir(directory),
                button_color=MDApp.get_running_app().theme_cls.primary_color,
                duration=10,
            )
            self.snackbar.show()
        self.ids.export_dir_text_field.text = MDApp.get_running_app().apkg_export_dir

    def set_export_dir(self, directory):
        """Set new export dir to value ``directory``."""
        self.snackbar.duration = 0
        os.makedirs(directory, exist_ok=True)
        MDApp.get_running_app().apkg_export_dir = directory
        self.ids.export_dir_text_field.text = directory
