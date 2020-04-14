import lorem
from kivy.animation import Animation
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty, ObjectProperty, Property
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior, CircularRippleBehavior
from kivymd.uix.card import MDCard

Builder.load_file("mychooser.kv")


class CheckBehavior(object):
    class CheckElement(ButtonBehavior, ThemableBehavior):
        checked = BooleanProperty(False)
        text_color = ListProperty([0, 0, 0, 1])
        bg_color = ListProperty([1, 1, 1, 1])
        text = StringProperty(lorem.paragraph())
        checked_state = Property({})
        unchecked_state = Property({})

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

        def on_checked(self, *args):
            if self.checked:
                anim = Animation(**self.checked_state, duration=0.5, t="out_circ")
            else:
                anim = Animation(**self.unchecked_state, duration=0.5, t="out_circ")
            anim.start(self)


class CheckElement(ButtonBehavior, ThemableBehavior):
    checked = BooleanProperty(False)
    text_color = ListProperty([0, 0, 0, 1])
    bg_color = ListProperty([1, 1, 1, 1])
    text = StringProperty(lorem.paragraph())
    checked_state = Property({})
    unchecked_state = Property({})

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

    def on_checked(self, *args):
        if self.checked:
            anim = Animation(**self.checked_state, duration=0.5, t="out_circ")
        else:
            anim = Animation(**self.unchecked_state, duration=0.5, t="out_circ")
        anim.start(self)


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


# class MyCheckImageTile(CheckElement,SmartTile):
#     pass
#
# class MyCheckImageTileContainer(CheckContainer,ThemableBehavior,GridLayout):
#     CheckContainer = MyCheckImageTile


if __name__ == "__main__":
    class TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            return Builder.load_string("""
#:import lorem lorem
ScrollView:
    do_scroll_x: False
    do_scroll_y: True
    size_hint: 1,1
    MyCheckChipContainer:
        id: container
        check_one: True
        string_list: ["test_"+str(i) for i in range(10)]
""")


    TestApp().run()
