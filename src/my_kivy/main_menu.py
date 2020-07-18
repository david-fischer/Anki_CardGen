"""
Implements :class:`MainMenu`.
"""

import os

from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.stacklayout import StackLayout
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import MDList, OneLineIconListItem

from my_kivy.mychooser import CheckBehavior, CheckContainer
from utils import widget_by_id


class DrawerItem(CheckBehavior, OneLineIconListItem):
    """List item that changes color based on :attr:`current_state`."""

    icon = StringProperty()
    """:class:`~kivy.properties.StringProperty`: name of icon."""

    name = StringProperty("test")
    """:class:`~kivy.properties.StringProperty`: name of the screen."""

    path = StringProperty("")
    """:class:`~kivy.properties.StringProperty`: path of the screens kv-file."""

    def __init__(self, **kwargs):
        super(DrawerItem, self).__init__(**kwargs)
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
        """changes color of clicked item and updates :attr:`current`"""
        super(DrawerList, self).conditional_uncheck(instance, value)
        self.current = instance.name


class MainMenu(StackLayout):
    """Contains everything related to the NavigationDrawer and the Screens."""

    screen_dicts = ListProperty(
        [
            {
                "icon": "form-textbox",
                "text": "Manual Input",
                "name": "screen_single_word",
                "path": "my_kivy/screen_single_word.kv",
            },
            {
                "icon": "format-list-checkbox",
                "text": "Queue",
                "name": "screen_queue",
                "path": "my_kivy/screen_queue.kv",
            },
            {
                "icon": "cogs",
                "text": "Settings",
                "name": "screen_settings",
                "path": "my_kivy/screen_settings.kv",
            },
        ]
    )
    """:class:`~kivy.properties.ListProperty` containing the dictionaries describing all screens."""

    def on_parent(self, *_):
        """
        This function sets up the screens using ``name`` and ``path`` from :attr:`screen_dicts`.

        The screens are added to the screen_man and corresponding entries to the drawer_list.
        Then :attr:`DrawerList.current` is bound to screen_man.current and vice-versa.
        """
        for screen_dict in self.screen_dicts:
            screen = KvScreen(**{key: screen_dict[key] for key in ["name", "path"]})
            self.ids.screen_man.add_widget(screen)
        self.ids.drawer_list.child_dicts = self.screen_dicts
        self.ids.drawer_list.bind(current=self.ids.screen_man.setter("current"))
        self.ids.screen_man.bind(current=self.ids.drawer_list.setter("current"))
        self.ids.drawer_list.children[-1].on_release()


class KvScreen(Screen):
    path = StringProperty("my_kivy/screen_default.kv")

    def __init__(self, **kwargs):
        super(KvScreen, self).__init__(**kwargs)
        if not os.path.exists(self.path):
            self.create_content_file()
        self.load_content()

    def load_content(self):
        self.add_widget(Builder.load_file(self.path))

    def create_content_file(self):
        with open(self.path, "w") as file:
            file.write(f'MDLabel:\n\ttext:"{self.name}"')


Factory.register("KvScreen", KvScreen)
