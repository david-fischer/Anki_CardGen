"""Implements :class:`SettingsRoot`, the root widget for the settings screen."""
from time import sleep

from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.picker import MDThemePicker

from utils import app_busy


class SettingsRoot(BoxLayout):
    """Root widget of the settings screen."""

    theme_dialog = ObjectProperty()

    def __init__(self, **kwargs):
        super(SettingsRoot, self).__init__(**kwargs)
        self.theme_dialog = MDThemePicker()
        self.theme_dialog.ids.close_button.bind(
            on_press=MDApp.get_running_app().save_theme
        )

    @staticmethod
    @app_busy
    def sleep_some():
        """Test-function."""
        sleep(5)
