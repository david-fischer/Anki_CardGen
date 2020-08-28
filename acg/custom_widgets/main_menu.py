"""Implements :class:`MainMenu`."""

import os

import toolz
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import MDList, OneLineIconListItem
from kivymd.uix.menu import MDDropdownMenu

from custom_widgets.behaviors import CheckBehavior
from custom_widgets.selection_widgets import CheckContainer
from db import get_template_names
from paths import SCREEN_DIR
from utils import widget_by_id


# print(SCREEN_DIR)
# print(__file__)
# print(os.getcwd())
# print(os.listdir("."))
# input()


class DrawerItem(CheckBehavior, OneLineIconListItem):
    """List item that changes color based on :attr:`current_state`."""

    icon = StringProperty()
    """:class:`~kivy.properties.StringProperty`: name of icon."""

    name = StringProperty("test")
    """:class:`~kivy.properties.StringProperty`: name of the screen."""

    kv_file_name = StringProperty("")
    """:class:`~kivy.properties.StringProperty`: name of the screens kv-file."""

    def __init__(self, **kwargs):
        super(DrawerItem, self).__init__(**kwargs)
        self.current_state = False
        self.theme_cls.bind(theme_style=self.on_current_state)
        self.theme_cls.bind(primary_palette=self.on_current_state)

    def on_release(self):
        """Close drawer and sets :attr:`current_state` to ``True``."""
        self.current_state = True
        widget_by_id("nav_drawer").set_state("close")


Factory.register("DrawerItem", DrawerItem)


class DrawerList(ThemableBehavior, CheckContainer, MDList):
    """
    List containing :class:`DrawerItem`.

    It has one active element at all times whose screen_name attribute is saved in :attr:`current`.
    """

    check_one = True
    child_class_name = "DrawerItem"
    current = StringProperty("")
    """:class:`~kivy.properties.StringProperty` of currently active :attr:`DrawerItem.screen_name`."""

    def conditional_uncheck(self, instance, value):
        """Change color of clicked item and updates :attr:`current`."""
        super(DrawerList, self).conditional_uncheck(instance, value)
        if value:
            self.current = instance.name

    def on_current(self, *_):
        """Change the state of the children respectively to :attr:`current`."""
        current_widget = [
            child
            for child in self.root_for_children.children
            if child.name == self.current
        ][0]
        current_widget.current_state = True
        self.conditional_uncheck(current_widget, False)


class MainMenu(StackLayout):
    """Contains everything related to the NavigationDrawer and the Screens."""

    screen_dicts = ListProperty(
        [
            {
                "icon": "form-textbox",
                "text": "Manual Input",
                "name": "single_word",
                "kv_file_name": "single_word.kv",
            },
            {
                "icon": "format-list-checkbox",
                "text": "Queue",
                "name": "queue",
                "kv_file_name": "queued.kv",
            },
            {
                "icon": "history",
                "text": "History",
                "name": "history",
                "kv_file_name": "history.kv",
            },
            {
                "icon": "cogs",
                "text": "Settings",
                "name": "settings",
                "kv_file_name": "settings.kv",
            },
        ]
    )
    """:class:`~kivy.properties.ListProperty` containing the dictionaries describing all screens."""

    screens = ListProperty()

    def __init__(self, **kwargs):
        super(MainMenu, self).__init__(**kwargs)
        print(get_template_names())
        self.dropdown_menu = MDDropdownMenu(
            caller=self.ids.current_template_drop,
            items=[{"text": name} for name in get_template_names()],
            position="center",
            width_mult=4,
        )
        self.dropdown_menu.on_release = print
        self.dropdown_menu.bind(on_release=self.on_dropdown_item)

    def on_dropdown_item(self, _, item):
        """Close menu and set app.current_template_name."""
        MDApp.get_running_app().current_template_name = item.text
        self.dropdown_menu.dismiss()

    def on_parent(self, *_):
        """
        Set up screen using ``name`` and ``path`` from :attr:`screen_dicts`.

        The screens are added to the screen_man and corresponding entries to the drawer_list.
        Then :attr:`DrawerList.current` is bound to screen_man.current and vice-versa.
        """
        # for screen_dict in self.screen_dicts:
        self.screens = [
            KvScreen(**{key: screen_dict[key] for key in ["name", "kv_file_name"]})
            for screen_dict in self.screen_dicts
        ]
        # self.ids.screen_man.add_widget(screen)
        self.ids.drawer_list.data = self.screen_dicts
        self.ids.drawer_list.bind(current=self.set_screen)
        # self.ids.drawer_list.bind(current=self.ids.screen_man.setter("current"))
        self.ids.screen_man.bind(current=self.ids.drawer_list.setter("current"))
        self.ids.drawer_list.children[-1].on_release()

    def set_screen(self, _, screen_name):
        """Switch screens dynamically."""
        self.ids.screen_man.switch_to(self.get_screen(screen_name))

    def get_screen(self, screen_name):
        """Return screen by name."""
        return [screen for screen in self.screens if screen.name == screen_name][0]

    def get_item_text(self, screen):
        """Get the text of the :class:`DrawerItem` corresponding to a screen."""
        if not screen:
            return None
        screen_dict = toolz.first(
            screen_dict
            for screen_dict in self.screen_dicts
            if screen_dict["name"] == screen.name
        )
        return screen_dict["text"]

    def get_screen_names(self):
        """Return screen names."""
        return [screen.name for screen in self.screens]


class KvScreen(Screen):
    """
    Screen that automatically adds content of kv-file at :attr:`path` as child.

    If :attr:`path` does not exist, create file.
    """

    kv_file_name = StringProperty("screen_default.kv")
    """:class:`~kivy.properties.StringProperty` defaults to ``"screen_default.kv"`` """

    def __init__(self, **kwargs):
        super(KvScreen, self).__init__(**kwargs)
        self.path = os.path.join(SCREEN_DIR, self.kv_file_name)
        self.size_hint = None, 1
        self.width = Window.width
        Window.bind(width=self.setter("width"))
        if not os.path.exists(self.path):
            self._create_content_file()
        self._load_content()

    def _load_content(self):
        self.add_widget(Builder.load_file(self.path))

    def _create_content_file(self):
        with open(self.path, "w") as file:
            file.write(f'MDLabel:\n\ttext:"{self.name}"')


Factory.register("KvScreen", KvScreen)