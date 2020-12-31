"""Implements :class:`SettingsRoot`, the root widget for the settings screen."""
from ..custom_widgets import PathSection, SectionBase, SettingsWidget, ThemeSection
from ..custom_widgets.behaviors import ChildrenFromDataBehavior
from ..design_patterns.factory import CookBook

section_cookbook = CookBook()
section_cookbook.register("Theme")(ThemeSection)
section_cookbook.register("Paths")(PathSection)


@section_cookbook.register("Template")
class TemplateSection(SectionBase, ChildrenFromDataBehavior):
    """Not implemented yet."""

    # TODO: implement


class SettingsRoot(SettingsWidget):
    """Root widget of the settings screen."""

    cookbook = section_cookbook
