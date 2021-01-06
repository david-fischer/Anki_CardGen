"""Implements :class:`MainMenu`."""


import os

import toolz
from kivy.lang import Builder
from kivy.properties import DictProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import MDList, OneLineIconListItem
from kivymd.uix.menu import MDDropdownMenu

from .behaviors import CheckBehavior, ChildrenFromDataBehavior


class DrawerItem(CheckBehavior, OneLineIconListItem):
    """List item that changes color based on :attr:`current_state`."""

    icon = StringProperty()
    """:class:`~kivy.properties.StringProperty`: name of icon."""

    name = StringProperty("test")
    """:class:`~kivy.properties.StringProperty`: name of the screen."""

    kv_file_name = StringProperty("")
    """:class:`~kivy.properties.StringProperty`: name of the screens kv-file."""


class DrawerList(ThemableBehavior, ChildrenFromDataBehavior, MDList):
    """
    List containing :class:`DrawerItem`.

    It has one active element at all times whose screen_name attribute is saved in :attr:`current`.
    """

    check_one = True
    child_class_name = "DrawerItem"
    current = StringProperty("")
    """:class:`~kivy.properties.StringProperty` of currently active :attr:`DrawerItem.screen_name`."""
    nav_drawer = ObjectProperty()

    def on_child_release(self, instance):
        """Set states of child's according to :attr:`check_one`.

        Gets called if a child dispatches `on_release`-event.
        """
        if self.check_one:
            for child in self.children:
                child.current_state = child == instance
        else:
            instance.current_state = not instance.current_state
        self.current = instance.name
        self.nav_drawer.set_state("close")

    def on_current(self, *_):
        """Update state of :attr:`current` by calling :meth:´on_child_release´."""
        current_child = self.get_child(self.current)
        if not current_child.current_state:
            self.on_child_release(current_child)


class MainMenu(StackLayout):
    """Contains everything related to the NavigationDrawer and the Screens."""

    screen_dicts = ListProperty()
    """:class:`~kivy.properties.ListProperty` containing the dictionaries describing all screens."""

    screens = DictProperty()
    screen_dir = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dropdown_menu = MDDropdownMenu(
            caller=self.ids.current_template_drop,
            items=[{"text": name} for name in MDApp.get_running_app().templates],
            position="center",
            width_mult=4,
        )
        self.dropdown_menu.on_release = print
        self.dropdown_menu.bind(on_release=self.on_dropdown_item)

    def on_dropdown_item(self, _, item):
        """Close menu and set app.current_template_name."""
        MDApp.get_running_app().current_template_name = item.text
        self.dropdown_menu.dismiss()

    def _init_screens(self):
        for screen_dict in self.screen_dicts:
            name = screen_dict["name"]
            kv_path = os.path.join(self.screen_dir, name) + ".kv"
            self.screens[name] = KvScreen(name=name, kv_path=kv_path)

    def on_parent(self, *_):
        """
        Set up screen using ``name`` and ``path`` from :attr:`screen_dicts`.

        The screens are added to the screen_man and corresponding entries to the drawer_list.
        Then :attr:`DrawerList.current` is bound to screen_man.current and vice-versa.
        """
        self._init_screens()
        self.ids.drawer_list.data = self.screen_dicts
        self.ids.drawer_list.bind(current=self.set_screen)
        self.ids.screen_man.bind(current=self.ids.drawer_list.setter("current"))
        current_screen = self.ids.drawer_list.children[-1].name
        self.set_screen(screen_name=current_screen)

    def set_screen(self, _=None, screen_name=""):
        """Switch screens dynamically."""
        self.ids.screen_man.switch_to(self.get_screen(screen_name))

    def get_screen(self, screen_name):
        """Return screen by name."""
        return self.screens[screen_name]

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
        return list(self.screens)

    @staticmethod
    def get_right_action_items(screen):
        r"""Return ``right_action_items`` attribute of ``screen``\ s root widget if present. Else return empty list."""
        try:
            return screen.children[0].right_action_items
        except (KeyError, AttributeError, IndexError):
            return []


class KvScreen(Screen):
    """
    Screen that automatically adds content of kv-file at :attr:`path` as child.

    If :attr:`path` does not exist, create file.
    """

    kv_path = StringProperty("screen_default.kv")
    """:class:`~kivy.properties.StringProperty` defaults to ``"screen_default.kv"`` """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # TODO: TEST WEATHER THIS HAS A USE!!
        # self.size_hint = None, 1
        # self.width = Window.width
        # Window.bind(width=self.setter("width"))
        if not os.path.exists(self.kv_path):
            self._create_content_file()
        self._load_content()

    def _load_content(self):
        self.add_widget(Builder.load_file(self.kv_path))

    def _create_content_file(self):
        with open(self.kv_path, "w") as file:
            file.write(f'MDLabel:\n\ttext:"{self.name}"')
