import os

from kivy.animation import Animation
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    Property, StringProperty,
)
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
    this_directory = os.path.dirname(__file__)
    Builder.load_file(os.path.join(this_directory, "mychooser.kv"))


# TODO: GENERALIZE TO MULTI-STATE OBJECT AND DERIVE 2-STATE OBJECT AS SPECIAL CASE+
class MultiStateBehaviour:
    possible_states = ListProperty()
    current_state = Property("")
    state_dicts = DictProperty()
    animated_properties = ListProperty()

    def __init__(self, **kwargs):
        if "state_dicts" in kwargs:
            self.state_dicts = kwargs["state_dicts"]
        if "current_state" in kwargs:
            self.current_state = kwargs["current_state"]
        init_state = self.state_dicts[self.current_state]
        # print(vars(self),init_state,kwargs)
        super(MultiStateBehaviour, self).__init__(**init_state, **kwargs)

    def on_current_state(self, current_state):
        animation_dict = {
            key: val
            for key, val in self.state_dicts[current_state]
            if key in self.animated_properties
        }
        for key, val in self.state_dicts[current_state]:
            if key not in self.animated_properties:
                setattr(self, key, val)
        anim = Animation(**animation_dict, duration=0.5, t="out_circ")
        anim.start(self)


class CheckBehavior:
    checked = BooleanProperty(False)
    checked_state = DictProperty()
    unchecked_state = DictProperty()

    def __init__(self, **kwargs):
        state = self.checked_state if self.checked else self.unchecked_state
        super(CheckBehavior, self).__init__(**kwargs, **state)

    def on_checked(self, *_):
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
            "bg_color":   self.theme_cls.bg_darkest
                          if self.theme_cls.theme_style == "Light"
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
            for check_element in [
                others for others in self.children if others != instance and value
            ]:
                check_element.checked = False

    def get_checked(self, property_name=None):
        checked_elements = [
            element for element in self.children[::-1] if element.checked
        ]
        if property_name is None:
            return checked_elements
        return [getattr(element, property_name) for element in checked_elements]

    def on_element_dicts(self, *_):
        self.clear_widgets()
        for elem_dict in self.element_dicts:
            new_check_element = self.CheckElementObject(**elem_dict)
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
            "bg_color":   self.theme_cls.bg_darkest
                          if self.theme_cls.theme_style == "Light"
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
    IMG_STRING = """
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
    TRANS_CARD_STRING = """
BoxLayout:
    MyTransCardContainer:
        element_dicts: [{"text_orig":("text_orig_"+str(i))*10,"text_trans": ("text_trans_"+str(i))*10} for i in 
        range(10)]    
"""

    CHECK_CARD_STRING = """
BoxLayout:
    MyCheckCardContainer:
        element_dicts: [{"text":("text_orig_"+str(i))*10, "checked":True} for i in range(10)]    
    """

    TRANS_CHIP_STRING = """
BoxLayout:
    MyTransChipContainer:
        element_dicts: [{"text_orig":("text_orig_"+str(i))*10,"text_trans": ("text_trans_"+str(i))*10} for i in 
        range(10)]
"""


    class TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            return Builder.load_string(TRANS_CARD_STRING)


    TestApp().run()
