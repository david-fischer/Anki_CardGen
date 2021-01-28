"""ImportChains."""
from collections import defaultdict
from typing import Callable

import attr
import toolz
from bs4 import BeautifulSoup
from kivy.factory import Factory
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager

from .custom_widgets.dialogs import CustomDialog
from .design_patterns.callback_chain import CallChain, CallNode, PrinterNode
from .design_patterns.factory import CookBook
from .language_processing import lemma_dict, remove_punctuation
from .utils import get_file_manager, pop_unchanged

COLOR2MEANING = {
    "highlight_yellow": "words",
    "highlight_blue": "phrases",
    "highlight_pink": "sentences",
    "highlight_orange": "",
}
MEANING2COLOR = {val: key for key, val in COLOR2MEANING.items()}


def dict_from_kindle_export(file_path):
    """
    Extract highlighted parts and sorts them by color in a dictionary.

    Args:
      file_path: Path to an html-file exported from kindle.

    Returns:
        :Dictionary `{"highlight_color_1" : ["list", "of" , "highlighted parts", ...],...}`
    """
    with open(file_path) as file:
        soup = BeautifulSoup(file, "lxml")
    heading_tags = soup.select("div.noteHeading span")
    highlight_dict = defaultdict(list)
    for tag in heading_tags:
        highlight_dict[tag["class"][0]].append(tag.find_next().text.strip())
    return highlight_dict


node_cookbook = CookBook()
import_chain_cookbook = CookBook()

node_cookbook.register("Printer")(PrinterNode)


@attr.s(auto_attribs=True)
class FileManagerNode(CallNode):
    """Opens file_manager and calls next node with selected file."""

    config_key: str = "kobo_import_dir"
    ext: list = [".txt", ".annot", ".html"]

    def receive(self):  # pylint: disable=arguments-differ
        """Open file_manager with :meth:`send` as callback."""
        path = MDApp.get_running_app().config["Paths"][self.config_key]
        with get_file_manager(ext=self.ext, callback=self.send) as file_manager:
            file_manager.show(path=path)


def clean_words(words: list):
    """Clean up list of words by removal of punctuation and empty strings."""
    words = [remove_punctuation(word).lower() for word in words]
    return [word for word in words if word]


@node_cookbook.register("Lemmatizer")
@attr.s(auto_attribs=True)
class Lemmatizer(CallNode):
    """Send dictionary with suggested replacements and list of unchanged words to next node."""

    language: str = "pt"
    is_new: Callable = lambda item: True

    def process(self, words: list):  # pylint: disable=arguments-differ
        """Send dictionary with suggested replacements and list of unchanged words to next node."""
        lemmas = lemma_dict(words)
        lemmas = toolz.itemfilter(self.is_new, lemmas)
        unchanged = pop_unchanged(lemmas)
        self.send(unchanged=unchanged, replacements=lemmas)


@node_cookbook.register(
    "TextInput",
    dialog_cls_name="TextInputDialog",
    title="Input comma-seperated words:",
)
@attr.s(auto_attribs=True)
class DialogNode(CallNode):
    """Open Dialog with received suggested replacements and sends unchanged words + chosen words to next node."""

    dialog: CustomDialog = None
    title: str = "TITLE:"
    dialog_cls_name: str = "CustomDialog"

    def _init_dialog(self):
        self.dialog = Factory.get(self.dialog_cls_name)(
            title=self.title,
            callback=self.dialog_callback,
        )

    def dialog_callback(self, button, result):
        """Callback-function for dialog."""
        if button == "OK":
            self.send(result)

    def get_dialog_data(self, *args, **kwargs):
        """Get right format for dialog."""

    def process(self, *args, **kwargs):
        """Open Dialog with received suggested replacements and sends unchanged words + chosen words to next node."""
        if not self.dialog:
            self._init_dialog()
        self.dialog.set_data(self.get_dialog_data(*args, **kwargs))
        print(self.dialog.content_cls.data)
        self.dialog.content_cls.data = self.dialog.content_cls.data
        self.dialog.open()


# TODO: Default yes vs default no
@node_cookbook.register("CheckChipDialog")
@attr.s(auto_attribs=True)
class CheckChipDialogNode(DialogNode):
    """Open dialog to filter selection with CheckChips."""

    dialog_cls_name: str = "CheckChipDialog"
    title: str = "Select items:"

    def get_dialog_data(self, elements):  # pylint: disable=arguments-differ
        """Return data to construct CheckChips from."""
        return [{"text": text} for text in elements]


@node_cookbook.register("ReplacementDialog")
@attr.s(auto_attribs=True)
class ReplacementDialogNode(DialogNode):
    """Open Dialog with received suggested replacements and sends unchanged words + chosen words to next node."""

    unchanged: list = None
    height: int = 45
    title: str = (
        "Some words are not in their dictionary form."
        "The following replacements are suggested:"
    )
    dialog_cls_name: str = "ReplacementDialog"

    def dialog_callback(self, button, result):
        """Callback-function for dialog."""
        if button == "OK":
            self.send(self.unchanged + result)

    def get_dialog_data(self, replacements):  # pylint: disable = arguments-differ
        """Get right format for dialog."""
        return [
            {"word": key, "lemma": val, "height": self.height}
            for key, val in replacements.items()
        ]

    def process(self, unchanged, replacements):  # pylint: disable=arguments-differ
        """Open Dialog with received suggested replacements and sends unchanged words + chosen words to next node."""
        self.unchanged = unchanged
        if replacements:
            super().process(replacements)
        else:
            self.send(unchanged)


def word_list_from_kindle(path):
    """
    Use :const:`MEANING2COLOR` `["words"]` to extract the list of words highlighted in this specific color.

    Args:
      path: Path to html-file exported by kindle.

    Returns:
      : List of highlighted words.
    """
    color = MEANING2COLOR["words"]
    return dict_from_kindle_export(path)[color]


def word_list_from_txt(path):
    """
    Return list of words read as lines from txt-file.

    Args:
      path: Path to txt-file. Each line should correspond to a word (or phrase).
    """
    with open(path) as file:
        words = file.read().splitlines()
    return words


def word_list_from_kobo(path):
    """Parse kobos .annot-file and return list of notations."""
    with open(path) as file:
        soup = BeautifulSoup(file, "lxml")
    words = [tag.text for tag in soup.select("annotation text")]
    return words


replace_lemmas_nodes = [clean_words, "Lemmatizer", "ReplacementDialog"]

node_dict = {
    "kobo": {
        "nodes": [
            FileManagerNode(config_key="kobo_import_dir"),
            word_list_from_kobo,
        ]
        + replace_lemmas_nodes,
        "info": {"icon": "book-open-outline", "text": "Import from Kobo"},
    },
    "kindle": {
        "nodes": [
            FileManagerNode(config_key="import_dir"),
            word_list_from_kindle,
        ]
        + replace_lemmas_nodes,
        "info": {"icon": "book-open-variant", "text": "Import from kindle"},
    },
    "txt": {
        "nodes": [FileManagerNode(config_key="import_dir"), word_list_from_txt]
        + replace_lemmas_nodes,
        "info": {"icon": "file-document-outline", "text": "Import from txt"},
    },
    "text_input": {
        "nodes": ["TextInput", lambda x: [w.strip() for w in x.split(",")]]
        + replace_lemmas_nodes,
        "info": {"icon": "cursor-text", "text": "Import from Text Input"},
    },
}
for key, val in node_dict.items():
    import_chain_cookbook.register(key, cookbook=node_cookbook, **val)(CallChain)

#
# pylint: disable = W,C,R,I,E
if __name__ == "__main__":
    for d in import_chain_cookbook.to_button_dict().values():
        print(d["callback"])

    from .custom_widgets.custom_speed_dial import CustomSpeedDial

    c = CustomSpeedDial

    class _Example(MDApp):
        dialog = None
        file_manager = None
        importer = None
        target_language = "pt"

        def build(self):
            self.file_manager = MDFileManager()
            self.speed_dial_data = import_chain_cookbook.to_button_dict()

            return Builder.load_string(
                """
FloatLayout:

    MDFlatButton:
        text: "PICK FILE"
        pos_hint: {'center_x': .5, 'center_y': .3}
        on_release: app.importer()

    CustomSpeedDial:
        button_dict: app.speed_dial_data"""
            )

    _Example().run()
