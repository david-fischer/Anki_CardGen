"""Implements :class:`HistoryMain`, the root widget of the history screen."""
import os

from bidict import bidict
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.toast import toast
from pony.orm import db_session

from db import export_cards
from utils import not_implemented_toast


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
        super(HistoryRoot, self).__init__(**kwargs)
        Clock.schedule_once(self.__post_init__)

    def __post_init__(self, *_):
        self.speed_dial.icon = "content-save"

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
