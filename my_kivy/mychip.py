from kivy.lang import Builder
from kivy.properties import (
    StringProperty,
    ListProperty,
    ObjectProperty,
    BooleanProperty,
    NumericProperty)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import CircularRippleBehavior

Builder.load_file("mychip.kv")


class MyChip(CircularRippleBehavior, ButtonBehavior, BoxLayout, ThemableBehavior):
    label = StringProperty()
    icon = StringProperty("")
    color = ListProperty()
    check = BooleanProperty(False)
    callback = ObjectProperty()
    radius = NumericProperty("12dp")
    selected = BooleanProperty(False)
    unselected_chip_color = ListProperty()
    selected_chip_color = ListProperty()
    text_color = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.unselected_chip_color:
            self.unselected_chip_color = self.theme_cls.bg_light
        if not self.selected_chip_color:
            self.selected_chip_color = self.theme_cls.primary_color

    def on_icon(self, instance, value):
        if value == "":
            self.icon = "checkbox-blank-circle"
            self.remove_widget(self.ids.icon)

    def on_press(self, *args):
        if self.parent.choose_one:
            for chip in self.parent.children:
                chip.selected = False
            self.selected = True

        else:
            self.selected = not self.selected

        print(self.parent.get_selected())


class MyChooseChip(StackLayout):
    choose_one = BooleanProperty("True")

    def get_selected(self):
        return [chip.label
                for chip in self.children
                if chip.selected
                ]


if __name__ == "__main__":
    class TestApp(MDApp):
        def build(self):
            return Builder.load_string("""

BoxLayout:
    orientation: "vertical"
    padding: 20,20
    spacing: 20
    MyChooseChip:
        choose_one: False
        MyChip:
            label: "Test"
            icon: "plus"
        MyChip:
    
    MyChooseChip:
        choose_one: True
        MyChip:
            label: "1"
            icon: "plus"
        MyChip:
            label: "2"
            icon: "plus"
        MyChip:
            label: "3"
            icon: "plus"
        MyChip:
            label: "4"
            icon: "plus"

""")


    TestApp().run()
