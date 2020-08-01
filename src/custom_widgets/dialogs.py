"""Provides :class:`CustomDialog` and :class:`ReplacementContent`."""
import os
from functools import partial

from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog

from custom_widgets.scroll_widgets import ScrollList

try:
    Builder.load_file("custom_widgets/dialogs.kv")
except FileNotFoundError:
    this_directory = os.path.dirname(__file__)
    Builder.load_file(os.path.join(this_directory, "dialogs.kv"))


class ReplacementItem(ButtonBehavior, BoxLayout):
    """
    Item displaying a word (:attr:`word`) and a possible replacement (:attr:`lemma`).

    :attr:`lemma` can be edited and the selection of word vs replacement switches on click.
    """

    lemma = StringProperty("")
    """:class:`~kivy.properties.StringProperty` defaults to ``""``."""
    word = StringProperty("")
    """:class:`~kivy.properties.StringProperty` defaults to ``""``."""
    take_lemma = BooleanProperty(False)
    """:class:`~kivy.properties.BooleanProperty` defaults to ``False``. Indicates user choice."""
    edit = BooleanProperty(False)
    """:class:`~kivy.properties.BooleanProperty` defaults to ``False``. While ``True`` the :attr:`lemma` can be
    edited."""

    def on_press(self, *_):
        """Placeholder-function."""


class DialogContent(ScrollList):
    """Content for the :class:`CustomDialog` class."""

    child_class_name = "ReplacementItem"
    data = ListProperty(
        [{"word": f"word_{i}", "lemma": f"lemma{i}"} for i in range(10)]
    )
    """:class:`~kivy.properties.ListProperty`.``"""

    def __init__(self, **kwargs):
        self.register_event_type("on_item_press")
        self.child_bindings["on_press"] = partial(self.dispatch, "on_item_press")
        super(DialogContent, self).__init__(**kwargs)

    def on_item_press(self, *_):
        """Placeholder-function."""

    def get_result(self):
        """Placeholder-function."""


class ReplacementContent(DialogContent):
    """Content for the ReplacementDialog."""

    child_class_name = StringProperty("ReplacementItem")
    """:class:`~kivy.properties.StringProperty` defaults to ``"ReplacementItem"``."""

    def get_result(self):
        """Get user selection."""
        return [
            (child.lemma if child.take_lemma else child.word)
            for child in self.root_for_children.children[::-1]
        ]


class CustomDialog(MDDialog):
    """Custom dialog."""

    type = "custom"
    button_cls_name = StringProperty("DialogButton")
    """:class:`~kivy.properties.StringProperty` defaults to ``"DialogButton"``."""
    button_texts = ListProperty(["OK", "CANCEL"])
    """:class:`~kivy.properties.ListProperty` defaults to ``["OK", "CANCEL"]``."""
    callback = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty` defaults to ````."""
    auto_dismiss = False
    """Do not dismiss on click outside the dialog."""

    def __init__(self, **kwargs):
        button_cls = Factory.get(self.button_cls_name)
        self.buttons = [
            button_cls(text=button_text) for button_text in self.button_texts
        ]
        for button in self.buttons:
            button.bind(on_press=self.on_button_press)
        super(CustomDialog, self).__init__(**kwargs)
        self.content_cls.bind(on_item_press=self.on_item_press)

    def on_button_press(self, obj):
        """Placeholder-function."""
        self.callback(obj.text, self.content_cls.get_result())
        self.dismiss()

    def on_item_press(self, *_):
        """Placeholder-function."""


# pylint: disable = W,C,R,I,E
if __name__ == "__main__":

    class _Example(MDApp):
        dialog = None

        def build(self):
            return Builder.load_string(
                """
FloatLayout:

    MDFlatButton:
        text: "ALERT DIALOG"
        pos_hint: {'center_x': .5, 'center_y': .5}
        on_release: app.show_confirmation_dialog()
"""
            )

        def show_confirmation_dialog(self):
            if not self.dialog:
                self.dialog = CustomDialog(
                    title="test", content_cls=ReplacementContent(), callback=print
                )
            self.dialog.content_cls.data = [
                {"word": "aguento", "lemma": "aguentar"},
                {"word": "deixa", "lemma": "deixar"},
                {"word": "caminhada", "lemma": "caminhar"},
                {"word": "pedras", "lemma": "pedrar"},
                {"word": "almoçamos", "lemma": "almoçar"},
                {"word": "limpinho", "lemma": "limpo"},
                {"word": "quedas d’água", "lemma": "quedo d’água"},
                {"word": "ansiosos", "lemma": "ansioso"},
            ]
            self.dialog.open()

    _Example().run()
