"""CustomSpeedDial."""
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import AliasProperty, DictProperty
from kivymd.uix import SpecificBackgroundColorBehavior
from kivymd.uix.button import MDFloatingActionButtonSpeedDial


class CustomSpeedDial(MDFloatingActionButtonSpeedDial, SpecificBackgroundColorBehavior):
    """Small changes to MDFloatingActionButtonSpeedDial.

    Define callbacks in dictionary for each button individually.
    """

    button_dict = DictProperty({"book-open": {"callback": print, "text": "test"}})

    def _get_data(self):
        """Getter-function for AliasProperty."""
        return {str(i): str(v["text"]) for i, v in self.button_dict.items()}

    data = AliasProperty(getter=_get_data, bind=["button_dict"])

    def callback(self, button):
        """Callback-function when any button is pressed."""
        self.close_stack()
        self.button_dict[button.icon]["callback"]()


Factory.register("CustomSpeedDial", CustomSpeedDial)
Builder.load_string(
    """
<CustomSpeedDial>:
    label_text_color: self.specific_text_color
    background_palette: "Accent"
"""
)
