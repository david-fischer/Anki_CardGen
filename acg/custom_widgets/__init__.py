import pathlib

from kivy.factory import Factory
from kivy.lang import Builder

from .custom_speed_dial import CustomSpeedDial
from .dialogs import (
    CheckChipContent,
    CheckChipDialog,
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
from .selection_widgets import CheckChipContainer, LongPressImage, TransCard

# selection_widgets
from .settings import PathSection, SectionBase, SettingsWidget, ThemeSection

Factory.register("LongPressImage", LongPressImage)
Factory.register("TransCard", TransCard)
Factory.register("CustomSpeedDial", CustomSpeedDial)
# scroll_widgets
Factory.register("ScrollBox", ScrollBox)
Factory.register("ScrollGrid", ScrollGrid)
Factory.register("RecycleViewBox", RecycleViewBox)
Factory.register("LeftStatusIndicatorListItem", LeftStatusIndicatorListItem)
# dialogs
Factory.register("CheckChipContent", CheckChipContent)
Factory.register("CheckChipDialog", CheckChipDialog)
Factory.register("TextInputDialog", TextInputDialog)
Factory.register("CustomContentBase", CustomContentBase)
Factory.register("CustomDialog", CustomDialog)
Factory.register("ReplacementItemsContent", ReplacementItemsContent)
Factory.register("ReplacementDialog", ReplacementDialog)
# main_menu
Factory.register("DrawerItem", DrawerItem)
Factory.register("KvScreen", KvScreen)
# settings
Factory.register("SettingsWidget", SettingsWidget)
Factory.register("PathSection", PathSection)
Factory.register("ThemeSection", ThemeSection)
Factory.register("SectionBase", SectionBase)

for kv_file in pathlib.Path(__file__).parent.glob("**/*.kv"):
    Builder.unload_file(str(kv_file))
    Builder.load_file(str(kv_file))
