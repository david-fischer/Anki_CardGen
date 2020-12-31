"""Provides widgets to display and change the config nicely.

How to use:
    * Define Sections(SectionBase) and add to cookbook with section-tile of config as name
    * For each key in this section, that should be editable, add some widget(KeyBase) and
    * Define SettingsRoot(SettingsWidget)
"""

import pathlib

from kivy.config import ConfigParser
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    DictProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.picker import MDThemePicker

from ..utils import get_file_manager  # TODO: make independent of ..utils
from .behaviors import ChildrenFromDataBehavior
from .selection_widgets import SeparatorWithHeading


class SectionBase(BoxLayout):
    """Base-class for Section of Settings.

    Should correspond to a section of :class:`kivy.config.ConfigParser`.
    """

    config = ObjectProperty()
    section = StringProperty()
    _config_update = BooleanProperty()

    def _get_data(self):
        return [
            {"key": key, "val": val} for key, val in self.config[self.section].items()
        ]

    data = AliasProperty(getter=_get_data, bind=["config", "_config_update"])

    def update_config(self, *_, key=None, val=None):
        """Set :attr:`config` value if `key` and `val` are specified."""
        if key and val:
            self.config.set(self.section, key, val)
            self.config.write()
            # the following is a workaround, because on_config is only triggered on re-assignment
            # and not on change:
            self._config_update = not self._config_update


class KeyBase(Widget):
    """Base-class for Widget that triggers the change of a single config key."""

    key = StringProperty()
    val = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_update")

    def dispatch_update(self, val):
        """Dispatch ``on_update`` event, so that parent-widget knows which config-entry to update."""
        self.dispatch("on_update", key=self.key, val=val)

    def on_update(self, *_, **kwargs):
        """Placeholder-function."""


class PathChooser(KeyBase, BoxLayout):
    """Key (as Label) and Button that opens a file-manager."""

    def choose_path(self):
        """Open file manager. Call :meth:`dispatch_update` with chosen folder as new val."""
        with get_file_manager(
            ext=[".*"], callback=self.dispatch_update
        ) as file_manager:
            path = pathlib.Path(self.val)
            path = path if path.exists() else pathlib.Path(".")
            path = str(path.absolute())
            file_manager.show(path=path)


class SettingsWidget(BoxLayout):
    """Base-class for SettingsRoot screen."""

    config = ObjectProperty()
    sections = DictProperty()
    cookbook = ObjectProperty()

    def add_section(self, section_name: str):
        """Add section by name. Must be contained in :attr:`cookbook`."""
        section = self.cookbook.cook(section_name, config=self.config)
        self.sections[section_name] = section
        self.add_widget(SeparatorWithHeading(heading=section_name))
        self.add_widget(section)

    def on_config(self, *_):
        """Add add sections from :attr:`config`."""
        for section_name in self.config:
            if section_name in self.cookbook.get_recipe_names():
                self.add_section(section_name)


class ThemeSection(SectionBase):
    """Section that changes the current theme."""

    theme_dialog = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_dialog = MDThemePicker()


class PathSection(ChildrenFromDataBehavior, SectionBase):
    """Section ``"Paths"`` of the config."""

    child_class_name = "PathChooser"
    section = "Paths"

    def __init__(self, **kwargs):
        self.child_bindings = {"on_update": self.update_config}
        super().__init__(**kwargs)


# pylint: disable = W,C,R,I,E
if __name__ == "__main__":
    from .. import CONFIG_PATH
    from ..design_patterns.factory import CookBook

    config = ConfigParser()
    config.read(str(CONFIG_PATH))
    settings_sections_cookbook = CookBook()
    settings_sections_cookbook.register("Theme")(ThemeSection)
    settings_sections_cookbook.register("Paths")(PathSection)

    class _TestApp(MDApp):
        def get_application_config(self):
            super().get_application_config(defaultpath=CONFIG_PATH)

        def build(self):
            self.file_manager = MDFileManager()
            return SettingsWidget(config=config, cookbook=settings_sections_cookbook)

    _TestApp().run()
