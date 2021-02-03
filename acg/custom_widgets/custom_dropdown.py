"""Implement CustomDropdownMenu and open_dropdown_menu."""
from kivy.properties import DictProperty
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu


class CustomDropdownMenu(MDDropdownMenu):
    """Slightly improved syntax."""

    callbacks = DictProperty()

    def __init__(self, **kwargs):
        kwargs.setdefault("position", "center")
        kwargs.setdefault("width_mult", 4)
        super().__init__(**kwargs)

    def on_release(self, item, *_):
        """Call function corresponding to clicked item in dropdown menu."""
        self.callbacks[item.text](self.caller)
        self.dismiss()

    def on_callbacks(self, *_):
        """Update items with current keys in :attr:`callbacks`."""
        self.items = [  # pylint: disable=attribute-defined-outside-init
            {"text": key} for key in self.callbacks
        ]


def open_dropdown_menu(item, **kwargs):
    """Open the apps' dropdown menu."""
    dropdown_menu = MDApp.get_running_app().dropdown_menu
    if not dropdown_menu:
        dropdown_menu = CustomDropdownMenu()
        MDApp.get_running_app().dropdown_menu = dropdown_menu
    dropdown_menu.caller = item  # pylint: disable=attribute-defined-outside-init
    dropdown_menu.callbacks = kwargs
    dropdown_menu.open()
