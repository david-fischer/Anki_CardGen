from ..design_patterns.factory import CookBook
from .exporter import APKGExporter, is_in_history, is_new

export_cookbook = CookBook()

export_cookbook.register(
    "export_select",
    selector=lambda c: False,
    info={"icon": "check-box-multiple-outline", "text": "select cards to export"},
)(APKGExporter)
export_cookbook.register(
    "export_all",
    selector=is_in_history,
    info={"icon": "content-save-all", "text": "export all cards"},
)(APKGExporter)
export_cookbook.register(
    "export_new",
    selector=is_new,
    info={"icon": "new-box", "text": "export new cards"},
)(APKGExporter)

anki_templates = {
    "davids_template": "vocab_card",
    "georgs_template": "vocab_card_georg",
}
