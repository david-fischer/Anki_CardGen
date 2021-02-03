"""Implements :class:`HistoryMain`, the root widget of the history screen."""

from kivy.clock import Clock
from kivy.properties import DictProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from pony.orm import db_session

from ..custom_widgets.dialogs import TextInputDialog
from ..exporter import export_cookbook
from ..utils import app_busy, not_implemented_toast, set_word_state


class HistoryRoot(FloatLayout):
    """Root widget of the history screen."""

    speed_dial_buttons = DictProperty()
    speed_dial = ObjectProperty()
    export_cookbook = export_cookbook

    def __init__(self, **kwargs):
        self.speed_dial_buttons = self.export_cookbook.to_button_dict()
        super().__init__(**kwargs)
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *_):
        self.speed_dial.icon = "content-save"
        self.dropdown_menu = MDDropdownMenu(
            caller=self.ids.history_list,
            position="center",
            width_mult=4,
            items=[
                {"text": "back to queue"},
                {"text": "delete"},
                {"text": "edit"},
            ],
        )
        self.dropdown_menu.on_release = self.on_dropdown_item
        self.text_input_dialog = TextInputDialog(title="Edit Word:")
        self.text_input_dialog.callback = self.text_input_dialog_callback
        # self.dropdown_menu.bind(on_release=self.on_dropdown_item)

    @staticmethod
    def filter(*_):
        """Placeholder-function."""
        not_implemented_toast()

    @staticmethod
    def sort(*_):
        """Placeholder-function."""
        not_implemented_toast()

    def click_on_item(self, item, *_):
        """Open dropdown menu with ``item`` as caller."""
        self.dropdown_menu.caller = item
        self.dropdown_menu.open()

    def on_dropdown_item(self, item, *_):
        """Call option corresponding to clicked item."""
        caller = self.dropdown_menu.caller
        if item.text == "delete":
            self.delete_item(caller.text)
        elif item.text == "edit":
            self.edit_item(caller.text)
        else:
            self.move_back_to_queue(caller.text)
        self.dropdown_menu.dismiss()

    @staticmethod
    def delete_item(item):
        """Delete ``text`` from the current template in the data-base and from ``app.word_state_dict``."""
        app = MDApp.get_running_app()
        del app.word_state_dict[item]
        with db_session:
            app.get_current_template_db().get_card(item).delete()

    @app_busy
    def edit_item(self, item):
        """Open :attr:`text_input_dialog` to edit the word."""
        self.text_input_dialog.default_text = item
        self.text_input_dialog.open()

    @staticmethod
    def move_back_to_queue(item):
        """Move item back to queue."""
        old_state = MDApp.get_running_app().word_state_dict[item]
        new_state = "waiting" if old_state == "error" else "ready"
        set_word_state(item, new_state)

    def text_input_dialog_callback(self, button_txt, text):
        """If the ``OK``-button is pressed, delete old entry and add edited entry to queue."""
        if button_txt == "OK":
            self.delete_item(self.text_input_dialog.default_text)
            set_word_state(text, "waiting")
