import os

from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior, ThemeManager
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineAvatarListItem, OneLineIconListItem
from kivymd.uix.picker import MDThemePicker

from anki.generate_anki_card import AnkiObject
from my_kivy.mychooser import CheckBehavior, CheckContainer
from utils import widget_by_id
from word_requests.pt_word import Word


def set_screen(screen_name):
    widget_by_id("screen_man").current = screen_name


Builder.load_file("my_kivy/screens.kv")


class DrawerItem(CheckBehavior, OneLineIconListItem):
    icon = StringProperty()
    screen_name = StringProperty("test")

    def __init__(self, **kwargs):
        super(DrawerItem, self).__init__()
        self.checked_state = {"text_color": self.theme_cls.primary_color}
        self.unchecked_state = {"text_color": self.theme_cls.text_color}
        super(DrawerItem, self).__init__(**kwargs)

    def on_release(self):
        self.checked = True
        widget_by_id("nav_drawer").set_state("close")


class DrawerList(ThemableBehavior, CheckContainer, MDList):
    check_one = True
    CheckElementObject = DrawerItem
    current = StringProperty("")

    def conditional_uncheck(self, instance, value):
        super(DrawerList, self).conditional_uncheck(instance, value)
        self.current = instance.screen_name

    def click_screen_name(self, screen_name):
        for item in self.children:
            if item.screen_name == screen_name:
                item.on_release()


class MainMenu(StackLayout):
    screen_dicts = ListProperty(
        [{"icon": "script-text-outline", "text": "Import from Kindle Notes", "screen_name": "screen_import"},
         {"icon": "textbox", "text": "Single Word", "screen_name": "screen_single_word"},
         {"icon": "cogs", "text": "Settings", "screen_name": "screen_settings"},
         # {"icon": "folder", "text": "My files", "screen_name": "my_files"},
         ]
    )

    def set_screen(self, screen_name):
        self.ids.screen_man.current = screen_name

    def on_parent(self, *args):
        for screen_dict in self.screen_dicts:
            name = screen_dict["screen_name"]
            path = f"my_kivy/{name}.kv"
            screen = Screen(name=name, id=name)
            if not os.path.exists(path):
                with open(path, "w") as file:
                    file.write(f'MDLabel:\n\ttext:"{name}"')
            screen.add_widget(Builder.load_file(path))
            self.ids.screen_man.add_widget(screen)
        self.ids.drawer_list.element_dicts = self.screen_dicts
        self.ids.drawer_list.bind(current=self.ids.screen_man.setter("current"))
        self.ids.drawer_list.children[-1].on_release()


class AnkiCardGenApp(MDApp):
    word = ObjectProperty()
    dialog = ObjectProperty()
    anki = ObjectProperty()
    theme_dialog = ObjectProperty()

    def show_dialog(self, message, options, callback, button_function=None):
        if button_function is None:
            def button_function(obj):
                callback(obj.text)
                self.dialog.dismiss()

        items = [OneLineAvatarListItem(text=option, on_press=button_function) for option in options]
        self.dialog = MDDialog(
            title=message,
            type="simple",
            items=items,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=self.theme_cls.primary_color, on_press=lambda x: self.dialog.dismiss()
                ),
            ],
            auto_dismiss=False,
        )
        self.dialog.ids.title.color = self.theme_cls.text_color
        self.dialog.open()

    def on_config_change(self, config, section, key, value):
        if config is self.config:
            token = (section, key)
            if token == ('Layout', 'Color'):
                print('Color has been changed to', value)
            elif token == ('Layout', 'Style'):
                print('Style has been changed to', value)

    def build_config(self, config):
        config.setdefaults('Theme', {
            'primary_palette': 'Red',
            'accent_palette':  'Yellow',
            'theme_style':     'Dark'
        })

    def build(self):
        config = self.config
        self.anki = AnkiObject(root_dir="anki")
        self.word = Word()
        self.theme_cls = ThemeManager(**config["Theme"])
        self.theme_dialog = MDThemePicker()
        self.theme_dialog.ids.close_button.bind(on_press=self.save_theme)
        return Builder.load_string("MainMenu:")

    def save_theme(self, *args):
        for key in self.config["Theme"]:
            self.config["Theme"][key] = getattr(self.theme_cls, key)
        self.config.write()

if __name__ == "__main__":
    AnkiCardGenApp().run()
