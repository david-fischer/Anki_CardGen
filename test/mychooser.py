import lorem
from kivy.animation import Animation
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty, ObjectProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior, CircularRippleBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.imagelist import SmartTile

Builder.load_file("mychooser.kv")


class CheckBehavior(object):
    checked = BooleanProperty(False)
    checked_state = {}
    unchecked_state = {}

    def on_checked(self, *args):
        if self.checked:
            anim = Animation(**self.checked_state, duration=0.5, t="out_circ")
        else:
            anim = Animation(**self.unchecked_state, duration=0.5, t="out_circ")
        anim.start(self)

    def on_parent(self, *args):
        self.on_checked()


class CheckElement(CheckBehavior, ButtonBehavior, ThemableBehavior):
    text_color = ListProperty([0, 0, 0, 1])
    bg_color = ListProperty([1, 1, 1, 1])
    text = StringProperty(lorem.paragraph())

    def __init__(self, **kwargs):
        super(CheckElement, self).__init__(**kwargs)
        self.checked_state = {
            "bg_color": self.theme_cls.primary_color,
            "text_color": [1, 1, 1, 1],
        }
        self.unchecked_state = {
            "bg_color": self.theme_cls.bg_darkest if self.theme_cls.theme_style == "Light"
            else self.theme_cls.bg_light,
            "text_color": self.theme_cls.secondary_text_color,
        }
        self.on_checked()

    def on_press(self):
        self.checked = not self.checked


class CheckContainer(Widget):
    check_one = BooleanProperty(False)
    string_list = ListProperty([])
    CheckElementObject = ObjectProperty(CheckElement)

    def conditional_uncheck(self, instance, value):
        if self.check_one:
            for check_element in [others for others in self.children if others != instance and value]:
                check_element.checked = False

    def get_checked(self):
        return [element.text for element in self.children[::-1] if element.checked]

    def on_string_list(self, *args):
        self.clear_widgets()
        for string in self.string_list:
            new_check_element = self.CheckElementObject(text=string)
            new_check_element.bind(checked=self.conditional_uncheck)
            self.add_widget(new_check_element)
        if self.check_one:
            self.children[-1].checked = True


class MyCheckCard(RectangularRippleBehavior, CheckElement, MDCard):
    pass


class MyCheckChip(CircularRippleBehavior, CheckElement, BoxLayout):
    icon = StringProperty("magnify")

    def on_press(self):
        super(MyCheckChip, self).on_press()
        print(self.parent.get_checked())


class MyCheckCardContainer(CheckContainer, BoxLayout):
    CheckElementObject = MyCheckCard


class MyCheckChipContainer(CheckContainer, StackLayout, ThemableBehavior):
    CheckElementObject = MyCheckChip


class MyCheckImageTile(CheckBehavior, SmartTile):
    checked_state = {"opacity": 1, "border_width": 3}
    unchecked_state = {"opacity": 0.8, "border_width": 0.01}
    text = StringProperty()
    source = text
    border_width = NumericProperty(0.01)

    def on_press(self):
        self.checked = not self.checked


class MyCheckImageGrid(CheckContainer, ThemableBehavior, GridLayout):
    CheckElementObject = MyCheckImageTile


if __name__ == "__main__":
    class TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            return Builder.load_string("""
#:import lorem lorem
FloatLayout:
    ScrollView:
        do_scroll_x: False
        do_scroll_y: True
        size_hint: 1,1
        MyCheckImageGrid:
            cols: 2
            id: image_grid
            row_default_height: (self.width - self.cols*self.spacing[0]) / self.cols *3/4
            row_force_default: True
            size_hint_y: None
            height: self.minimum_height
            padding: dp(4), dp(4)
            spacing: dp(4)
            check_one: True
            string_list: ["../assets/guitar.png" for i in range(10)]
            
    MDFloatingActionButton:
        pos_hint: {"center_x":0.5,"center_y":0.5}
        on_press: image_grid.string_list = ["../assets/Latte.jpg" for i in range(10)]


""")


    TestApp().run()
