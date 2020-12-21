"""Implements :class:`HistoryMain`, the root widget of the history screen."""
import os

from bidict import bidict
from custom_widgets.dialogs import TextInputDialog
from db import export_cards
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.menu import MDDropdownMenu
from pony.orm import db_session
from utils import app_busy, not_implemented_toast, set_word_state, widget_by_id


class HistoryRoot(FloatLayout):
    """Root widget of the history screen."""

    action_button_data = bidict(
        {
            "new-box": "export new cards",
            "content-save-all": "export all cards",
            "check-box-multiple-outline": "select specific cards to export",
        }
    )
    speed_dial = ObjectProperty()

    def __init__(self, **kwargs):
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

    def export_cards(self, button):
        """Depending on which button was pressed, exports one of the following.

            * all cards
            * all new cards (i.e. cards that have been generated but not exported)
            * custom selection of cards (NOT YET IMPLEMENTED)


        TODO: IMPLEMENT
        """
        self.speed_dial.close_stack()
        option = self.action_button_data[button.icon]
        if option == "export new cards":
            states = ["done"]
        elif option == "export all cards":
            states = ["done", "exported"]
        else:
            toast("NOT IMPLEMENTED YET.", 10)
            return False
        with db_session:
            app = MDApp.get_running_app()
            current_template = app.get_current_template_db()
            cards = current_template.get_cards_by_selector(lambda c: c.state in states)
            if not cards:
                toast("Empty Selection. Could not export cards.")
                return False
            print(os.path.exists(app.apkg_export_dir))
            export_cards(cards, app.apkg_export_dir, app.get_anki_template_dir())
        toast(f"Exported cards to {app.apkg_export_dir}.", 5)
        return True

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
        print(item.text)

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
            widget_by_id("queue").add_waiting(text)
