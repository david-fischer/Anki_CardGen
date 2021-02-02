import pathlib
from functools import partial

from ..importer import CheckChipDialogNode

EXPORTER_DIR = pathlib.Path(__file__).parent.absolute()
from ..design_patterns.callback_chain import CallChain
from ..design_patterns.factory import CookBook
from .exporter import export_cards, get_cards

export_cookbook = CookBook()

export_cookbook.register(
    "export_select",
    nodes=[get_cards, CheckChipDialogNode(), export_cards],
    info={"icon": "check-box-multiple-outline", "text": "select cards to export"},
)(CallChain)
export_cookbook.register(
    "export_all",
    nodes=[partial(get_cards, state={"done", "exported"}), export_cards],
    info={"icon": "content-save-all", "text": "export all cards"},
)(CallChain)
export_cookbook.register(
    "export_new",
    nodes=[partial(get_cards, state={"done"}), export_cards],
    info={"icon": "new-box", "text": "export new cards"},
)(CallChain)

anki_templates = {
    "davids_template": "vocab_card",
    "georgs_template": "vocab_card_georg",
}
