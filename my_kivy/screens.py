from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import MDList, OneLineIconListItem

from utils import widget_by_id

def set_screen(screen_name):
    widget_by_id("screen_man").current = screen_name

class ContentNavigationDrawer(BoxLayout):
    pass


class DrawerItem(OneLineIconListItem):
    icon = StringProperty()
    screen_name = StringProperty()

    def on_release(self):
        #super(DrawerItem, self).on_release()
        self.parent.set_color_item(self)
        widget_by_id("/nav_drawer/").set_state("toggle")
        set_screen(self.screen_name)


class DrawerList(ThemableBehavior, MDList):
    def set_color_item(self, instance_item):
        """Called when tap on a menu item."""

        # Set the color of the icon and text for the menu item.
        for item in self.children:
            if item.text_color == self.theme_cls.primary_color:
                item.text_color = self.theme_cls.text_color
                break
        instance_item.text_color = self.theme_cls.primary_color


class TestNavigationDrawer(MDApp):
    def build(self):
        return Builder.load_file("screens.kv")

    def on_start(self):
        nav_item_dicts = [
            {"icon": "script-text-outline", "text": "Import from Kindle Notes", "screen_name": "kindle_import"},
            {"icon": "textbox", "text": "Single Word", "screen_name": "single_word"},
            {"icon": "cogs", "text": "Settings", "screen_name": "settings"},
            #{"icon": "folder", "text": "My files", "screen_name": "my_files"},
        ]
        for nav_item_dict in nav_item_dicts:
            item = DrawerItem(**nav_item_dict)
            self.root.ids.content_drawer.ids.md_list.add_widget(
                item
            )
            widget_by_id("screen_man").add_widget(Builder.load_file(f'screen_{nav_item_dict["screen_name"]}.kv'))

TestNavigationDrawer().run()
