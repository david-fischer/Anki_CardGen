import pathlib

from kivy.factory import Factory
from kivy.lang import Builder

from .custom_speed_dial import CustomSpeedDial
from .dialogs import (
    CustomContentBase,
    CustomDialog,
    ReplacementDialog,
    ReplacementItemsContent,
    TextInputDialog,
)
from .main_menu import DrawerItem, KvScreen
from .scroll_widgets import (
    LeftStatusIndicatorListItem,
    RecycleViewBox,
    ScrollBox,
    ScrollGrid,
)
from .selection_widgets import LongPressImage, TransCard

# selection_widgets
Factory.register("LongPressImage", LongPressImage)
Factory.register("TransCard", TransCard)
Factory.register("CustomSpeedDial", CustomSpeedDial)
# scroll_widgets
Factory.register("ScrollBox", ScrollBox)
Factory.register("ScrollGrid", ScrollGrid)
Factory.register("RecycleViewBox", RecycleViewBox)
Factory.register("LeftStatusIndicatorListItem", LeftStatusIndicatorListItem)
# dialogs
Factory.register("TextInputDialog", TextInputDialog)
Factory.register("CustomContentBase", CustomContentBase)
Factory.register("CustomDialog", CustomDialog)
Factory.register("ReplacementItemsContent", ReplacementItemsContent)
Factory.register("ReplacementDialog", ReplacementDialog)
# main_menu
Factory.register("DrawerItem", DrawerItem)
Factory.register("KvScreen", KvScreen)

for kv_file in pathlib.Path(__file__).parent.glob("**/*.kv"):
    Builder.unload_file(str(kv_file))
    Builder.load_file(str(kv_file))
