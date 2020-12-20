"""Provides :class:`CustomDialog` and :class:`ReplacementItemsContent`."""
import os
from functools import partial

from custom_widgets.scroll_widgets import ScrollList
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
from paths import CUSTOM_WIDGET_DIR

Builder.unload_file(os.path.join(CUSTOM_WIDGET_DIR, "dialogs.kv"))
Builder.load_file(os.path.join(CUSTOM_WIDGET_DIR, "dialogs.kv"))


class CustomContentBase:
    """Base-class to be used for instances of :attr:`CustomDialog.content_cls`."""

    def get_result(self):
        """Placeholder-function."""


class TextFieldContent(CustomContentBase, BoxLayout):
    """:class:`kivy.uix.BoxLayout` containing a :class:`kivymd.uix.MDTextField`.

    For use as:attr:`kivymd.uix.dialog.content_cls`.
    """

    default_text = StringProperty("")

    def get_result(self):
        """Return current entry of the text_field."""
        return self.ids.text_field.text


class ItemsContent(ScrollList, CustomContentBase):
    """Scrollable list of items.

    Items dispatch ``on_press``-events and itself dispatches ``on_item_press`` event.
    """

    child_class_name = "BaseListItem"
    data = ListProperty()
    """:class:`~kivy.properties.ListProperty`."""

    def __init__(self, **kwargs):
        self.register_event_type("on_item_press")
        self.child_bindings["on_press"] = partial(self.dispatch, "on_item_press")
        super().__init__(**kwargs)

    def on_item_press(self, *_):
        """Placeholder-function."""


class ReplacementItemsContent(ItemsContent):
    """Content for the ReplacementDialog."""

    child_class_name = StringProperty("ReplacementItem")
    """:class:`~kivy.properties.StringProperty` defaults to ``"ReplacementItem"``."""

    def get_result(self):
        """Get user selection."""
        return [
            (child.lemma if child.take_lemma else child.word)
            for child in self.root_for_children.children[::-1]
        ]


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


class CustomDialog(MDDialog):
    """Custom dialog."""

    type = "custom"
    content_cls_name = StringProperty("CustomContentBase")
    button_cls_name = StringProperty("DialogButton")
    """:class:`~kivy.properties.StringProperty` defaults to ``"DialogButton"``."""
    button_texts = ListProperty(["OK", "CANCEL"])
    """:class:`~kivy.properties.ListProperty` defaults to ``["OK", "CANCEL"]``."""
    callback = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty` defaults to ``None``."""
    auto_dismiss = False
    """Do not dismiss on click outside the dialog."""

    def __init__(self, **kwargs):
        button_cls = Factory.get(self.button_cls_name)
        self.buttons = [
            button_cls(text=button_text) for button_text in self.button_texts
        ]
        for button in self.buttons:
            button.bind(on_press=self.on_button_press)
        if kwargs.get("content_cls_name"):
            kwargs.setdefault(
                "content_cls", Factory.get(kwargs.get("content_cls_name"))()
            )
        super().__init__(**kwargs)
        self.content_cls.bind(on_item_press=self.on_item_press)

    def on_button_press(self, obj):
        """Call :meth:`CustomDialog.callback`.

        The arguments are the text of the pressed button and the result of :attr:`content_cls`.``get_result``.
        """
        self.callback(obj.text, self.content_cls.get_result())
        self.dismiss()

    def on_item_press(self, content, item):
        """Placeholder-function."""

    def set_data(self, data):
        """Set data of :attr:`content_cls`."""
        self.content_cls.data = data


class ReplacementDialog(CustomDialog):
    """Dialog with optional replacements."""

    def __init__(self, **kwargs):
        kwargs["content_cls_name"] = "ReplacementItemsContent"
        super().__init__(**kwargs)


class TextInputDialog(CustomDialog):
    """Dialog with one text field."""

    default_text = StringProperty("")
    """:~kivy.properties.StringProperty: defaults to "", the default text entry in the :~kivymd.uix.MDTextField:."""

    def __init__(self, **kwargs):
        default_text = kwargs.pop("default_text") if "default_text" in kwargs else ""
        self.content_cls = TextFieldContent(default_text=default_text)
        self.bind(
            default_text=self.content_cls.setter(  # pylint: disable=no-member
                "default_text"
            )
        )
        super().__init__(**kwargs)


Factory.register("TextInputDialog", TextInputDialog)
Factory.register("CustomContentBase", CustomContentBase)
Factory.register("CustomDialog", CustomDialog)
Factory.register("ReplacementItemsContent", ReplacementItemsContent)
Factory.register("ReplacementDialog", ReplacementDialog)

# pylint: disable = W,C,R,I,E
if __name__ == "__main__":

    class _Example(MDApp):
        dialog = None

        def build(self):
            return Builder.load_string(
                """
FloatLayout:

    MDFlatButton:
        text: "REPLACEMENT DIALOG"
        pos_hint: {'center_x': .5, 'center_y': .3}
        on_release: app.show_repl_dialog()

    MDFlatButton:
        text: "TEXT DIALOG"
        pos_hint: {'center_x': .5, 'center_y': .6}
        on_release: app.show_text_dialog()
"""
            )

        def show_repl_dialog(self):
            self.dialog = CustomDialog(
                title="test", content_cls=ReplacementItemsContent(), callback=print
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

        def show_text_dialog(self):
            if isinstance(self.dialog, TextInputDialog):
                self.dialog.default_text = "second call to text_input_dialog"
            else:
                self.dialog = TextInputDialog(
                    title="test",
                    default_text="this is a test",
                    callback=print,
                )
            self.dialog.open()

    _Example().run()
