import os
import queue

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import DictProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior, ThemeManager
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list import MDList, OneLineIconListItem
from kivymd.uix.picker import MDThemePicker

from anki.generate_anki_card import AnkiObject
from my_kivy.mychooser import CheckBehavior, CheckContainer
from utils import now_string, smart_loader, smart_saver, widget_by_id
from word_requests.pt_word import Word

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
        [  # {"icon": "script-text-outline", "text": "Import from Kindle Notes", "screen_name": "screen_import"},
            {"icon": "textbox", "text": "Manual Input", "screen_name": "screen_single_word"},
            {"icon": "format-list-checkbox", "text": "Queue", "screen_name": "screen_queue"},
            {"icon": "cogs", "text": "Settings", "screen_name": "screen_settings"},
            # {"icon": "folder", "text": "My files", "screen_name": "my_files"},
        ]
    )

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
    # Kivy
    dialog = ObjectProperty()
    file_manager = ObjectProperty()
    theme_dialog = ObjectProperty()
    # Other Objects
    word = ObjectProperty()
    anki = ObjectProperty(AnkiObject(root_dir="anki"))
    q = ObjectProperty()
    # Data
    error_words = ListProperty([])
    queue_words = ListProperty([])
    loading_state_dict = DictProperty({})
    done_words = ListProperty([])
    keys_to_save = ListProperty(["queue_words", "done_words", "error_words", "loading_state_dict", "anki"])

    @mainthread
    def show_dialog(self, message, options=None, callback=print, item_function=None, buttons=None):
        if item_function is None:
            def item_function(obj):
                self.dialog.dismiss()
                callback(obj.text)
        if buttons is None:
            buttons = [MDFlatButton(text="CANCEL", text_color=self.theme_cls.primary_color,
                                    on_press=lambda x: self.dialog.dismiss(),
                                    )]
        items = [OneLineIconListItem(text=option, on_press=item_function) for option in options]
        self.dialog = MDDialog(
            title=message,
            type="simple",
            items=items,
            auto_dismiss=False,
            buttons=buttons,
        )
        self.dialog.ids.title.color = self.dialog.theme_cls.text_color
        self.dialog.open()

    def build_config(self, config):
        config.setdefaults('Theme', {
            'primary_palette': 'Red',
            'accent_palette':  'Yellow',
            'theme_style':     'Dark'
        })

    def build(self):
        # Config and Theme
        self.theme_cls = ThemeManager(**self.config["Theme"])
        self.theme_dialog = MDThemePicker()
        self.theme_dialog.ids.close_button.bind(on_press=self.save_theme)
        # Non Kivy Objects
        self.load_app_state()
        for key in self.keys_to_save:
            self.bind(**{key: lambda *args: self.save_by_config_key(key)})
        self.word = Word()
        self.q = queue.Queue()
        # Kivy Objects
        self.file_manager = MDFileManager()
        return Builder.load_string("MainMenu:")

    def save_theme(self, *args):
        for key in self.config["Theme"]:
            self.config["Theme"][key] = getattr(self.theme_cls, key)
        self.config.write()

    def open_file_manager(self, path="/", select_path=print, ext=None):
        print("opening file manager...")
        if ext is None:
            ext = [".html"]
        self.file_manager.ext = ext
        self.file_manager.select_path = select_path
        self.file_manager.show(path)

    def load_by_config_key(self, key):
        path = self.config["Paths"][key]
        return smart_loader(path)

    def save_by_config_key(self, key, obj=None):
        if obj is None:
            obj = getattr(self, key)
        path = self.config["Paths"][key]
        smart_saver(obj, path)

    def load_app_state(self):
        for key in self.keys_to_save:
            try:
                self.load_by_config_key(key)
            except FileNotFoundError:
                print(f"No existing file for {key}. Created new one.")
                self.save_by_config_key(key)

    def add_anki_card(self, result_dict):
        toast(f'Added card for "{result_dict["Word"]}" to Deck.', 10)
        self.save_by_config_key("generated", result_dict)
        self.anki.add_card(**result_dict)
        apkg_path = self.config["Paths"]["apkg"]
        apkg_bkp_path = f"{apkg_path[:-5]}_{now_string()}.apkg"
        self.anki.write_apkg(apkg_path)
        self.anki.write_apkg(apkg_bkp_path)
        self.save_by_config_key("anki")
        self.done_words.append(result_dict["Word"])


if __name__ == "__main__":
    AnkiCardGenApp().run()
