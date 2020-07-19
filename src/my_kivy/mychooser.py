import os
from functools import partial

from kivy.animation import Animation
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import AsyncImage
from kivy.uix.modalview import ModalView
from kivy.uix.recycleview import RecycleView
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import CircularRippleBehavior, RectangularRippleBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.imagelist import SmartTile

from my_kivy.behaviors import (
    CheckBehavior,
    ChildrenFromDictsBehavior,
    LongPressBehavior,
    ThemableColorChangeBehavior,
    TranslationOnCheckBehavior,
)

try:
    Builder.load_file("my_kivy/mychooser.kv")
except FileNotFoundError:
    this_directory = os.path.dirname(__file__)
    Builder.load_file(os.path.join(this_directory, "mychooser.kv"))


class CheckContainer(ChildrenFromDictsBehavior):
    """Test"""

    check_one = BooleanProperty(False)
    """:class:`~kivy.properties.BooleanProperty`"""

    def __init__(self, **kwargs):
        super(CheckContainer, self).__init__(**kwargs)
        self.child_bindings["current_state"] = self.conditional_uncheck

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


class MyCheckChipContainer(CheckContainer, ThemableBehavior, StackLayout):
    child_class_name = "MyCheckChip"


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


class TransCard(LongPressBehavior, MDCard, RectangularRippleBehavior):
    text_orig = StringProperty("")
    text_trans = StringProperty("")


class LongPressImage(ButtonBehavior, LongPressBehavior, AsyncImage):
    pass


Factory.register("LongPressImage", LongPressImage)
Factory.register("TransCard", TransCard)


class ScrollBox(ChildrenFromDictsBehavior, ScrollView):
    pass


class ScrollGrid(ChildrenFromDictsBehavior, ScrollView):
    pass


Factory.register("ScrollBox", ScrollBox)
Factory.register("ScrollGrid", ScrollGrid)


class RecycleViewBox(RecycleView):
    pass


Factory.register("RecycleViewBox", RecycleViewBox)


class MyCarousel(FloatLayout, ChildrenFromDictsBehavior):
    carousel = ObjectProperty()
    height_dict = DictProperty()
    recycle_view_name = StringProperty()
    recycle_view_data_class = StringProperty()
    modal = ModalView()

    def __init__(self, **kwargs):
        super(MyCarousel, self).__init__(**kwargs)
        self.child_bindings = {
            "height": self.update_height,
            "on_press": self.open_menu,
        }
        self.on_child_dicts()

    def before_add_child(self, child):
        self.bind(width=lambda *_: self.set_child_width(child))

    def after_add_child(self, child):
        self.set_child_width(child)

    def set_child_width(self, child, *_):
        width = self.width - self.ids.left_icon.width - self.ids.right_icon.width
        setattr(child, "width", width)

    def update_height(self, *_):
        pass

    def get_modal_content(self, size_hint=(1, None)):
        def f(i, *_):
            self.carousel.index = i
            self.modal.dismiss()

        data_dicts = [
            {**dict, "size_hint": size_hint, "on_press": partial(f, i)}
            for i, dict in enumerate(self.child_dicts)
        ]
        recycle_view_cls = Factory.get(self.recycle_view_name)
        recycle_view = recycle_view_cls()
        recycle_view.child_class_name = self.recycle_view_data_class
        recycle_view.child_dicts = data_dicts
        return recycle_view

    def on_child_dicts(self, *_):
        self.height_dict = {}
        super(MyCarousel, self).on_child_dicts(*_)

    def get_checked(self, property_name=None):
        checked_elements = [self.carousel.current_slide]
        if property_name is None:
            return checked_elements
        return [getattr(element, property_name) for element in checked_elements]

    def open_menu(self, *_):
        self.modal = ModalView()
        modal_content = self.get_modal_content()
        self.modal.add_widget(modal_content)
        self.modal.open()


class ImageCarousel(MyCarousel):
    def get_modal_content(self, size_hint=(1, 1)):
        return super(ImageCarousel, self).get_modal_content(size_hint=size_hint)


class CardCarousel(MyCarousel):
    def update_height(self, *_):
        if self.carousel.current_slide:
            new_height = self.carousel.current_slide.height + 24
            if self.height != new_height:
                anim = Animation(height=new_height, duration=0.5)
                anim.start(self)

    def on_child_dicts(self, *_):
        super(CardCarousel, self).on_child_dicts(*_)
        if self.carousel:
            self.carousel.index = 1
            self.carousel.index = 0


if __name__ == "__main__":

    CARD_CAROUSEL_STRING = (
        "BoxLayout:\n"
        "    CardCarousel:\n"
        '        child_dicts: [{"text_orig":str(i)*50*i,"text_trans":"Trans"} for i in range(10)]'
    )

    IMAGE_CAROUSEL_STRING = (
        "BoxLayout:\n"
        "    ImageCarousel:\n"
        '        child_dicts: [{"source":"../assets/AnkiCardGen.png"} for _ in range(5)]'
    )

    class TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            return Builder.load_string(CARD_CAROUSEL_STRING)

    TestApp().run()
