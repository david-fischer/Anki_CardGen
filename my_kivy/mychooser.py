from kivy.animation import Animation
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import CircularRippleBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.imagelist import SmartTile

try:
    Builder.load_file("my_kivy/mychooser.kv")
except FileNotFoundError:
    Builder.load_file("mychooser.kv")


# TODO: GENERALIZE TO MULTI-STATE OBJECT AND DERIVE 2-STATE OBJECT AS SPECIAL CASE
class CheckBehavior(object):
    checked = BooleanProperty(False)
    checked_state = {}
    unchecked_state = {}

    def __init__(self, **kwargs):
        state = self.checked_state if self.checked else self.unchecked_state
        super(CheckBehavior, self).__init__(**kwargs, **state)

    def on_checked(self, *args):
        if self.checked:
            anim = Animation(**self.checked_state, duration=0.5, t="out_circ")
        else:
            anim = Animation(**self.unchecked_state, duration=0.5, t="out_circ")
        anim.start(self)


class CheckElement(CheckBehavior, ButtonBehavior, ThemableBehavior):
    text_color = ListProperty([0, 0, 0, 1])
    bg_color = ListProperty([1, 1, 1, 1])
    text = StringProperty("test " * 15)

    def __init__(self, **kwargs):
        self.theme_cls = ThemableBehavior().theme_cls
        self.checked_state = {
            "bg_color":   self.theme_cls.primary_color,
            "text_color": [1, 1, 1, 1],
        }
        self.unchecked_state = {
            "bg_color":   self.theme_cls.bg_darkest if self.theme_cls.theme_style == "Light"
                          else self.theme_cls.bg_light,
            "text_color": self.theme_cls.secondary_text_color,
        }

        super(CheckElement, self).__init__(**kwargs)

    def on_press(self):
        self.checked = not self.checked


class CheckContainer(Widget):
    check_one = BooleanProperty(False)
    element_dicts = ListProperty([])
    CheckElementObject = ObjectProperty(CheckElement)

    def conditional_uncheck(self, instance, value):
        if self.check_one:
            for check_element in [others for others in self.children if others != instance and value]:
                check_element.checked = False

    def get_checked(self, property=None):
        checked_elements = [element for element in self.children[::-1] if element.checked]
        if property is None:
            return checked_elements
        else:
            return [getattr(element, property) for element in checked_elements]

    def on_element_dicts(self, *args):
        self.clear_widgets()
        for dict in self.element_dicts:
            new_check_element = self.CheckElementObject(**dict)
            new_check_element.bind(checked=self.conditional_uncheck)
            self.add_widget(new_check_element)
        # if self.check_one:
        #     self.children[-1].checked = True


class MyCheckCard(CheckBehavior, MDCard):
    text_color = ListProperty([0, 0, 0, 1])
    bg_color = ListProperty([1, 1, 1, 1])
    text = StringProperty("test " * 15)

    def __init__(self, **kwargs):
        self.theme_cls = ThemableBehavior().theme_cls
        self.checked_state = {
            "bg_color":   self.theme_cls.primary_color,
            "text_color": [1, 1, 1, 1],
        }
        self.unchecked_state = {
            "bg_color":   self.theme_cls.bg_darkest if self.theme_cls.theme_style == "Light"
                          else self.theme_cls.bg_light,
            "text_color": self.theme_cls.secondary_text_color,
        }
        super(MyCheckCard, self).__init__(**kwargs)

    def on_press(self):
        self.checked = not self.checked


class MyTransCard(MyCheckCard):
    text_orig = StringProperty()
    text_trans = StringProperty()

    def __init__(self, **kwargs):
        if "checked" in kwargs:
            self.checked = kwargs["checked"]
        text = kwargs["text_orig"] if self.checked else kwargs["text_trans"]
        if "text" not in kwargs:
            kwargs["text"] = text
        super(MyTransCard, self).__init__(**kwargs)

    def on_checked(self, *args):
        self.text = self.text_orig if self.checked else self.text_trans
        super(MyTransCard, self).on_checked(*args)


class MyCheckChip(CircularRippleBehavior, CheckElement, BoxLayout):
    icon = StringProperty("")

    def on_press(self):
        super(MyCheckChip, self).on_press()


class MyTransChip(MyCheckChip):
    text_orig = StringProperty()
    text_trans = StringProperty()

    def __init__(self, **kwargs):
        if "checked" in kwargs:
            self.checked = kwargs["checked"]
        text = kwargs["text_orig"] if self.checked else kwargs["text_trans"]
        if "text" not in kwargs:
            kwargs["text"] = text
        super(MyTransChip, self).__init__(**kwargs)

    def on_checked(self, *args):
        super(MyTransChip, self).on_checked(*args)
        self.text = self.text_orig if self.checked else self.text_trans


class MyCheckCardContainer(CheckContainer, ThemableBehavior, BoxLayout):
    CheckElementObject = MyCheckCard


class MyTransCardContainer(MyCheckCardContainer):
    CheckElementObject = MyTransCard


class MyCheckChipContainer(CheckContainer, ThemableBehavior, StackLayout):
    CheckElementObject = MyCheckChip


class MyTransChipContainer(CheckContainer, ThemableBehavior, StackLayout):
    CheckElementObject = MyTransChip


class MyCheckImageTile(CheckBehavior, SmartTile):
    checked_state = {"opacity": 1, "border_width": 3}
    unchecked_state = {"opacity": 0.8, "border_width": 0.01}
    border_width = NumericProperty(0.01)

    def on_press(self):
        self.checked = not self.checked


class MyCheckImageGrid(CheckContainer, ThemableBehavior, GridLayout):
    CheckElementObject = MyCheckImageTile


if __name__ == "__main__":
    img_string = """
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
            element_dicts: [{"source":"../assets/guitar.png"} for i in range(10)]
            
    MDFloatingActionButton:
        pos_hint: {"center_x":0.5,"center_y":0.5}
        on_press: image_grid.element_dicts = [{"source":"../assets/Latte.jpg"} for i in range(10)]

"""
    trans_card_string = """
BoxLayout:
    MyTransCardContainer:
        element_dicts: [{"text_orig":("text_orig_"+str(i))*10,"text_trans": ("text_trans_"+str(i))*10} for i in range(10)]    
"""

    check_card_string = """
BoxLayout:
    MyCheckCardContainer:
        element_dicts: [{"text":("text_orig_"+str(i))*10, "checked":True} for i in range(10)]    
    """

    trans_chip_string = """
BoxLayout:
    MyTransChipContainer:
        element_dicts: [{"text_orig":("text_orig_"+str(i))*10,"text_trans": ("text_trans_"+str(i))*10} for i in range(10)]
"""


    class TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            return Builder.load_string(trans_chip_string)


    TestApp().run()
