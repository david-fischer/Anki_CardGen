import lorem
from kivy.animation import Animation
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior, CircularRippleBehavior
from kivymd.uix.card import MDCard

Builder.load_file("mychooser.kv")


class CheckElement(ButtonBehavior, ThemableBehavior):
    checked = BooleanProperty(False)
    text_color = ListProperty()
    bg_color = ListProperty()
    text = StringProperty(lorem.paragraph())

    def __init__(self, **kwargs):
        super(CheckElement, self).__init__(**kwargs)
        self.text_color = self.theme_cls.text_color
        self.bg_color = self.theme_cls.bg_light

    def on_press(self):
        self.parent.conditional_uncheck(self)
        self.checked = not self.checked

    def on_checked(self, *args):
        anim = Animation(bg_color=self.theme_cls.primary_color if self.checked else self.theme_cls.bg_light,
                         text_color=[1, 1, 1, 1] if self.checked else self.theme_cls.text_color,
                         duration=0.5,
                         t="out_circ")
        anim.start(self)


class CheckContainer(Widget):
    check_one = BooleanProperty(False)
    string_list = ListProperty([])
    CheckElementObject = ObjectProperty(CheckElement)

    def conditional_uncheck(self, pressed_element):
        if self.check_one:
            for check_element in self.children:
                check_element.checked = False

    def get_checked(self):
        return [element.text for element in self.children[::-1] if element.checked]

    def on_string_list(self, *args):
        self.clear_widgets()
        for string in self.string_list:
            self.add_widget(self.CheckElementObject(text=string))
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


class MyCheckChipContainer(CheckContainer, StackLayout):
    CheckElementObject = MyCheckChip


if __name__ == "__main__":
    class TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Dark"  # "Purple", "Red"
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
