"""
Implements :class:`MainMenu`.
"""

import os

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

    screen_name = StringProperty("test")
    """:class:`~kivy.properties.StringProperty`: name of the screen."""

    def __init__(self, **kwargs):
        super(DrawerItem, self).__init__(**kwargs)
        self.theme_cls.bind(theme_style=self.__post_init__)
        self.theme_cls.bind(primary_palette=self.__post_init__)

    def __post_init__(self, *_):
        self.state_dicts = {
            True: {"text_color": self.theme_cls.primary_color},
            False: {"text_color": self.theme_cls.text_color},
        }
        super(DrawerItem, self).__post_init__()

    def on_release(self):
        """Close drawer and sets :attr:`current_state` to ``True``."""
        self.current_state = True
        widget_by_id("nav_drawer").set_state("close")


class DrawerList(ThemableBehavior, CheckContainer, MDList):
    """
    List containing :class:`DrawerItem`.

    It has one active element at all times whose screen_name attribute is saved in :attr:`current`.
    """

    check_one = True
    CheckElementObject = DrawerItem
    current = StringProperty("")
    """:class:`~kivy.properties.StringProperty` of currently active :attr:`DrawerItem.screen_name`."""

    def conditional_uncheck(self, instance, value):
        """changes color of clicked item and updates :attr:`current`"""
        super(DrawerList, self).conditional_uncheck(instance, value)
        self.current = instance.screen_name


class MainMenu(StackLayout):
    """Contains everything related to the NavigationDrawer and the Screens."""

    screen_dicts = ListProperty(
        [
            {
                "icon": "form-textbox",
                "text": "Manual Input",
                "screen_name": "screen_single_word",
            },
            {
                "icon": "format-list-checkbox",
                "text": "Queue",
                "screen_name": "screen_queue",
            },
            {"icon": "cogs", "text": "Settings", "screen_name": "screen_settings"},
        ]
    )
    """:class:`~kivy.properties.ListProperty` containing the dictionaries describing all screens."""

    def on_parent(self, *_):
        """
        This function sets up the screens using the words from :attr:`screen_dicts`.

        The screens are added to the screen_man and corresponding entries to the drawer_list.
        Then :attr:`DrawerList.current` is bound to screen_man.current and vice-versa.
        """
        for screen_dict in self.screen_dicts:
            name = screen_dict["screen_name"]
            path = f"my_kivy/{name}.kv"
            screen = Screen(name=name)
            if not os.path.exists(path):
                with open(path, "w") as file:
                    file.write(f'MDLabel:\n\ttext:"{name}"')
            screen.add_widget(Builder.load_file(path))
            self.ids.screen_man.add_widget(screen)
        self.ids.drawer_list.child_dicts = self.screen_dicts
        self.ids.drawer_list.bind(current=self.ids.screen_man.setter("current"))
        self.ids.screen_man.bind(current=self.ids.drawer_list.setter("current"))
        self.ids.drawer_list.children[-1].on_release()
