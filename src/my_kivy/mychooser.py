import os
from copy import copy
from functools import partial

from kivy import clock
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    Property,
    StringProperty,
)
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.carousel import Carousel
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.modalview import ModalView
from kivy.uix.recycleview import RecycleView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import CircularRippleBehavior, RectangularRippleBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.imagelist import SmartTile

try:
    Builder.load_file("my_kivy/mychooser.kv")
except FileNotFoundError:
    this_directory = os.path.dirname(__file__)
    Builder.load_file(os.path.join(this_directory, "mychooser.kv"))

from kivy.clock import Clock
from kivy.factory import Factory


class RecycleViewGrid(RecycleView):
    pass


class RecycleViewBox(RecycleView):
    pass


Factory.register("ImgRecycleView", RecycleViewGrid)
Factory.register("TransCardRecycleView", RecycleViewBox)


class LongPressBehavior(EventDispatcher):
    long_press_time = Factory.NumericProperty(1)

    def __init__(self, **kwargs):
        super(LongPressBehavior, self).__init__(**kwargs)
        self.register_event_type("on_long_press")

    def on_state(self, instance, value):
        try:
            super(LongPressBehavior, self).on_state(instance, value)
        except AttributeError:
            pass
        if value == "down":
            lpt = self.long_press_time
            self._clockev = Clock.schedule_once(self._do_long_press, lpt)
        else:
            self._clockev.cancel()

    def _do_long_press(self, dt):
        self.dispatch("on_long_press")

    def on_long_press(self, *largs):
        pass


class MultiStateBehaviour:
    current_state = Property(None)
    """:class:`~kivy.properties.Property`"""

    state_dicts = DictProperty(None)
    """:class:`~kivy.properties.DictProperty`"""

    animated_properties = ListProperty()
    """:class:`~kivy.properties.ListProperty`"""

    def __init__(self, **kwargs):
        super(MultiStateBehaviour, self).__init__(**kwargs)
        clock.Clock.schedule_once(self.__post_init__)

    def on_current_state(self, *_):
        animation_dict = {
            key: val
            for key, val in self.state_dicts[self.current_state].items()
            if key in self.animated_properties
        }
        for key, val in self.state_dicts[self.current_state].items():
            if key not in self.animated_properties:
                setattr(self, key, val)
        if animation_dict:
            anim = Animation(**animation_dict, duration=0.5, t="out_circ")
            anim.start(self)

    def __post_init__(self, *_):
        self.on_current_state()


class CheckBehavior(MultiStateBehaviour):
    def __init__(self, **kwargs):
        self.current_state = False
        self.state_dicts = (
            {True: {}, False: {}} if self.state_dicts is None else self.state_dicts
        )
        super(CheckBehavior, self).__init__(**kwargs)


class ChildrenFromDictsBehavior:
    child_dicts = ListProperty([])
    child_class_name = StringProperty([])
    parent_widget = ObjectProperty()
    bindings = DictProperty()

    def __init__(self, **kwargs):
        super(ChildrenFromDictsBehavior, self).__init__(**kwargs)
        if self.parent_widget is None:
            self.parent_widget = self
        self.on_element_dicts()

    def on_element_dicts(self, *_):
        self.parent_widget.clear_widgets()
        for child_dict in self.child_dicts:
            child_cls = Factory.get(self.child_class_name)
            new_child = child_cls(**child_dict)
            print(new_child)
            if self.bindings:
                new_child.bind(**self.bindings)
            self.parent_widget.add_widget(new_child)


class CheckContainer(Widget):
    """Test"""

    check_one = BooleanProperty(False)
    """:class:`~kivy.properties.BooleanProperty`"""

    element_dicts = ListProperty([])
    """:class:`~kivy.properties.ListProperty`"""

    CheckElementObject = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty`"""

    def conditional_uncheck(self, instance, value):
        if self.check_one:
            for check_element in [
                others for others in self.children if others != instance and value
            ]:
                check_element.current_state = False

    def get_checked(self, property_name=None):
        checked_elements = [
            element for element in self.children[::-1] if element.current_state
        ]
        if property_name is None:
            return checked_elements
        return [getattr(element, property_name) for element in checked_elements]

    def on_element_dicts(self, *_):
        self.clear_widgets()
        for elem_dict in self.element_dicts:
            new_check_element = self.CheckElementObject(**elem_dict)
            new_check_element.bind(current_state=self.conditional_uncheck)
            self.add_widget(new_check_element)
        # if self.check_one:
        #     self.children[-1].checked = True


class TranslationOnCheckBehavior:
    text_orig = StringProperty("orig")
    """:class:`~kivy.properties.StringProperty`"""

    text_trans = StringProperty("trans")
    """:class:`~kivy.properties.StringProperty`"""

    def __post_init__(self, *_):
        self.state_dicts[True]["text"] = self.text_orig
        self.state_dicts[False]["text"] = self.text_trans
        super(TranslationOnCheckBehavior, self).__post_init__()


class ThemableColorChangeBehavior:
    text_color = ListProperty([0, 0, 0, 1])
    """:class:`~kivy.properties.ListProperty`"""

    bg_color = ListProperty([1, 1, 1, 1])
    """:class:`~kivy.properties.ListProperty`"""

    animated_properties = ["bg_color", "text_color"]

    def __init__(self, **kwargs):
        super(ThemableColorChangeBehavior, self).__init__(**kwargs)
        self.theme_cls.bind(theme_style=self.__post_init__)
        self.theme_cls.bind(primary_palette=self.__post_init__)

    def __post_init__(self, *_):
        self.state_dicts[True]["bg_color"] = self.theme_cls.primary_color
        self.state_dicts[False]["bg_color"] = (
            self.theme_cls.bg_darkest
            if self.theme_cls.theme_style == "Light"
            else self.theme_cls.bg_light
        )
        self.state_dicts[True]["text_color"] = [1, 1, 1, 1]
        self.state_dicts[False]["text_color"] = self.theme_cls.secondary_text_color
        super(ThemableColorChangeBehavior, self).__post_init__()


class MyCheckCard(ThemableColorChangeBehavior, CheckBehavior, MDCard):
    text = StringProperty("test " * 15)
    """:class:`~kivy.properties.StringProperty`"""

    def on_press(self):
        self.current_state = not self.current_state


class MyTransCard(TranslationOnCheckBehavior, MyCheckCard):
    pass


class MyCheckChip(
    CircularRippleBehavior,
    ButtonBehavior,
    ThemableColorChangeBehavior,
    CheckBehavior,
    ThemableBehavior,
    BoxLayout,
):
    icon = StringProperty("")
    """:class:`~kivy.properties.StringProperty`"""

    text = StringProperty("Chip")
    """:class:`~kivy.properties.StringProperty`"""

    def on_press(self):
        self.current_state = not self.current_state


class MyTransChip(TranslationOnCheckBehavior, MyCheckChip):
    pass


class MyCheckCardContainer(CheckContainer, ThemableBehavior, BoxLayout):
    CheckElementObject = MyCheckCard


class MyTransCardContainer(MyCheckCardContainer):
    CheckElementObject = MyTransCard


class MyCheckChipContainer(CheckContainer, ThemableBehavior, StackLayout):
    CheckElementObject = MyCheckChip


class MyTransChipContainer(MyCheckChipContainer):
    CheckElementObject = MyTransChip


class MyCheckImageTile(CheckBehavior, SmartTile):
    border_width = NumericProperty(0.01)
    """:class:`~kivy.properties.NumericProperty`"""

    def __init__(self, **kwargs):
        self.state_dicts = {
            True: {"opacity": 1, "border_width": 3},
            False: {"opacity": 0.8, "border_width": 0.01},
        }
        super(MyCheckImageTile, self).__init__(**kwargs)

    def on_press(self):
        self.current_state = not self.current_state


class MyCheckImageGrid(CheckContainer, ThemableBehavior, GridLayout):
    CheckElementObject = MyCheckImageTile


class TransCard(LongPressBehavior, MDCard, RectangularRippleBehavior):
    text_orig = StringProperty("")
    text_trans = StringProperty("")


class LongPressImage(ButtonBehavior, LongPressBehavior, AsyncImage):
    pass


Factory.register("LongPressImage", LongPressImage)
Factory.register("TransCard", TransCard)


class MyCarousel(FloatLayout, ChildrenFromDictsBehavior):
    carousel = ObjectProperty()
    height_dict = DictProperty()
    recycle_view_name = StringProperty()
    recycle_view_data_class = StringProperty()

    def __init__(self, **kwargs):
        super(MyCarousel, self).__init__(**kwargs)
        self.bindings = {"height": self.update_height, "on_press": self.open_menu}
        self.on_element_dicts()

    def update_height(self, obj, value):
        if value != self.height:
            value += 48
        self.height_dict[str(obj)] = value
        self.height = max(100, *self.height_dict.values())

    def on_element_dicts(self, *_):
        self.height_dict = {}
        super(MyCarousel, self).on_element_dicts(*_)

    def get_checked(self, property_name=None):
        checked_elements = [self.current_slide]
        if property_name is None:
            return checked_elements
        return [getattr(element, property_name) for element in checked_elements]

    def open_menu(self, *_):
        modal = ModalView()

        def f(i):
            self.carousel.index = i
            modal.dismiss()

        data_dicts = [
            {**dict, "on_press": partial(f, i)}
            for i, dict in enumerate(self.child_dicts)
        ]
        recycle_view = Factory.get(self.recycle_view_name)  #   RecycleView()
        recycle_view.viewclass = self.recycle_view_data_class
        recycle_view.data = data_dicts
        modal.add_widget(recycle_view)
        modal.open()


if __name__ == "__main__":
    IMG_STRING = """
FloatLayout:
    RecycleView:
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
            element_dicts: [{"source":"../assets/AnkiCardGen.png"} for i in range(10)]

    MDFloatingActionButton:
        pos_hint: {"center_x":0.5,"center_y":0.5}
        on_press: image_grid.element_dicts = [{"source":"../assets/Latte.jpg"} for i in range(10)]

"""
    TRANS_CARD_STRING = (
        "BoxLayout:\n"
        "    MyTransCardContainer:\n"
        '        element_dicts: [{"text_orig":("text_orig_"+str(i))*10,"text_trans": ("text_trans_"+str('
        'i))*10,  "current_state": i%2==0} for i in range(10)]'
    )

    CHECK_CARD_STRING = (
        "BoxLayout:\n"
        "    MyCheckCardContainer:\n"
        '        element_dicts: [{"text":("text_orig_"+str(i))*10, "current_state":True} for i in range(10)]'
    )

    TRANS_CHIP_STRING = (
        "\n"
        "BoxLayout:\n"
        "    MyTransChipContainer:\n"
        '        element_dicts: [{"text_orig":("text_orig_"+str(i))*10,"text_trans": ("text_trans_"+str('
        "i))*10} for i in range(10)]"
    )

    CARD_CAROUSEL_STRING = (
        "BoxLayout:\n"
        "    MyCarousel:\n"
        '        child_class_name: "TransCard"\n'
        '        child_dicts: [{"text_orig":str(i)*100,"text_trans":"Trans"} for i in range(10)]'
    )

    IMAGE_CAROUSEL_STRING = (
        "#:import image kivy.uix.image.AsyncImage\n"
        "#:import Factory kivy.factory.Factory\n"
        "BoxLayout:\n"
        "    MyCarousel:\n"
        '        element_dicts: [{"source":"../assets/AnkiCardGen.png"} for _ in range(5)]'
    )

    class TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            return Builder.load_string(CARD_CAROUSEL_STRING)

    TestApp().run()
