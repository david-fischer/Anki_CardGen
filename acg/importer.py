"""ImportChains."""
from typing import Callable

import attr
import toolz
from kivy.factory import Factory
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager

from acg import HOME
from acg.custom_widgets.dialogs import CustomDialog
from acg.design_patterns.callback_chain import CallChain, CallNode
from acg.utils import (
    get_file_manager,
    lemma_dict,
    pop_unchanged,
    remove_punctuation,
    word_list_from_kobo,
)


@attr.s(auto_attribs=True)
class FileManagerNode(CallNode):
    """Opens file_manager and calls next node with selected file."""

    dir: str = str((HOME / "Nextcloud" / "Book-Annotations").absolute())
    ext: list = [".txt", ".annot", ".html"]

    def receive(self):  # pylint: disable=arguments-differ
        """Open file_manager with :meth:`send` as callback."""
        with get_file_manager(ext=self.ext, callback=self.send) as file_manager:
            file_manager.show(path=self.dir)


def clean_words(words: list):
    """Clean up list of words by removal of punctuation and empty strings."""
    words = [remove_punctuation(word).lower() for word in words]
    return [word for word in words if word]


@attr.s(auto_attribs=True)
class Lemmatizer(CallNode):
    """Send dictionary with suggested replacements and list of unchanged words to next node."""

    language: str = "pt"
    is_new: Callable = lambda item: True

    def process(self, words: list):  # pylint: disable=arguments-differ
        """Send dictionary with suggested replacements and list of unchanged words to next node."""
        # TODO: IMPLEMENT LANGUAGE DEPENDENT LEMMATIZATION
        lemmas = lemma_dict(words)
        lemmas = toolz.itemfilter(self.is_new, lemmas)
        unchanged = pop_unchanged(lemmas)
        self.send(unchanged=unchanged, replacements=lemmas)


@attr.s(auto_attribs=True)
class DialogNode(CallNode):
    """Open Dialog with received suggested replacements and sends unchanged words + chosen words to next node."""

    dialog: CustomDialog = None
    unchanged: list = None
    height: int = 45
    title: str = (
        "Some words are not in their dictionary form."
        "The following replacements are suggested:"
    )

    content_cls_name = "ReplacementItemsContent"

    def _init_dialog(self):
        self.dialog = Factory.CustomDialog(
            title=self.title,
            content_cls_name=self.content_cls_name,
            callback=self.dialog_callback,
        )

    def dialog_callback(self, button, result):
        """Callback-function for dialog."""
        if button == "OK":
            self.send(self.unchanged + result)

    def get_dialog_data(self, replacements):
        """Get right format for dialog."""
        return [
            {"word": key, "lemma": val, "height": self.height}
            for key, val in replacements.items()
        ]

    def process(self, unchanged, replacements):  # pylint: disable=arguments-differ
        """Open Dialog with received suggested replacements and sends unchanged words + chosen words to next node."""
        self.unchanged = unchanged
        if not self.dialog:
            self._init_dialog()
        self.dialog.set_data(self.get_dialog_data(replacements))
        self.dialog.open()


# pylint: disable = W,C,R,I,E
if __name__ == "__main__":

    class _Example(MDApp):
        dialog = None
        file_manager = None
        importer = None

        def build(self):
            self.file_manager = MDFileManager()
            self.importer = CallChain(
                nodes=[
                    FileManagerNode(),
                    word_list_from_kobo,
                    clean_words,
                    Lemmatizer(),
                    DialogNode(),
                    print,
                ]
            )

            return Builder.load_string(
                """
FloatLayout:

    MDFlatButton:
        text: "PICK FILE"
        pos_hint: {'center_x': .5, 'center_y': .3}
        on_release: app.importer()
"""
            )

    _Example().run()
