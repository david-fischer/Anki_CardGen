"""Implements various elements to get user selection."""
import os
from functools import partial

from kivy.animation import Animation
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import AsyncImage
from kivy.uix.modalview import ModalView
from kivy.uix.stacklayout import StackLayout
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import (
    CircularRippleBehavior,
    RectangularRippleBehavior,
)
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
    """Container for widgets with :class:`~my_kivy.behaviors.CheckBehavior`."""

    check_one = BooleanProperty(False)
    """:class:`~kivy.properties.BooleanProperty` defaults to ``False``. If ``True`` only one child can be selected."""

    def __init__(self, **kwargs):
        super(CheckContainer, self).__init__(**kwargs)
        self.child_bindings["current_state"] = self.conditional_uncheck

    def conditional_uncheck(self, instance, value):
        """Uncheck other widgets if :attr:`check_one` is ``True``."""
        if self.check_one:
            for check_element in [
                others for others in self.children if others != instance and value
            ]:
                check_element.current_state = False

    def get_checked(self, attribute_name=None):
        """
        Return current selection.

        Args:
            attribute_name: Name of attribute to return. Defaults to ``None``.

        Returns:
            :* If ``attribute_name`` is None:  List of selected children
            * Else: List of attribute values
        """
        checked_elements = [
            element for element in self.children[::-1] if element.current_state
        ]
        if attribute_name is None:
            return checked_elements
        return [getattr(element, attribute_name) for element in checked_elements]


class MyCheckCard(ThemableColorChangeBehavior, CheckBehavior, MDCard):
    """Selectable :~kivymd.uix.card.MDCard`. Select by click. Changes color on selection."""

    text = StringProperty("test " * 15)
    """:class:`~kivy.properties.StringProperty`."""

    def on_press(self):
        """Change boolean value of :attr:`self.current_state`."""
        self.current_state = (  # pylint: disable=attribute-defined-outside-init
            not self.current_state
        )


class MyTransCard(TranslationOnCheckBehavior, MyCheckCard):
    """Selectable :class:`~kivymd.uix.card.MDCard`. Select by click. Changes color and displayed text on click."""


class MyCheckChip(
    CircularRippleBehavior,
    ButtonBehavior,
    ThemableColorChangeBehavior,
    CheckBehavior,
    ThemableBehavior,
    BoxLayout,
):
    """Selectable Chip. Select by click. Change color on selection."""

    icon = StringProperty("")
    """:class:`~kivy.properties.StringProperty` defaults to ""."""

    text = StringProperty("")
    """:class:`~kivy.properties.StringProperty` defaults to ""."""

    def on_press(self):
        """Change boolean value of :attr:`current_state`."""
        self.current_state = (  # pylint: disable=attribute-defined-outside-init
            not self.current_state
        )


class MyTransChip(TranslationOnCheckBehavior, MyCheckChip):
    """Selectable Chip. Select by click. Change color and text on selection."""


class MyCheckChipContainer(CheckContainer, ThemableBehavior, StackLayout):
    """Container for :class:`MyCheckChip`s. Use :attr:`child_dict` to populate."""

    child_class_name = "MyCheckChip"


class MyCheckImageTile(CheckBehavior, SmartTile):
    """
    Selectable :class:`~kivymd.uix.imagelist.SmartTile`.

    Select by click. Changes :attr:`opacity` and :attr:`boarder_width` on selection.
    """

    border_width = NumericProperty(0.01)
    """:class:`~kivy.properties.NumericProperty` describing boarder-width of image tile."""

    def __init__(self, **kwargs):
        self.state_dicts = {
            True: {"opacity": 1, "border_width": 3},
            False: {"opacity": 0.8, "border_width": 0.01},
        }
        super(MyCheckImageTile, self).__init__(**kwargs)

    def on_press(self):
        """Change boolean value of current state on press."""
        self.current_state = (  # pylint: disable=attribute-defined-outside-init
            not self.current_state
        )


class TransCard(LongPressBehavior, MDCard, RectangularRippleBehavior):
    """Displays :attr:`text_orig` and :attr:`text_trans`, separated by a line."""

    text_orig = StringProperty("")
    """:class:`~kivy.properties.StringProperty` first text."""

    text_trans = StringProperty("")
    """:class:`~kivy.properties.StringProperty` second text."""

    orientation = OptionProperty("vertical", options=["vertical", "horizontal"])
    """:class:`~kivy.properties.OptionProperty` possible values ["vertical", "horizontal"] defaults to "vertical"."""


class LongPressImage(LongPressBehavior, AsyncImage):
    """:class:`~kivy.uix.image.AsyncImage` with additional "on_press" and "on_long_press" event."""


Factory.register("LongPressImage", LongPressImage)
Factory.register("TransCard", TransCard)


class MyCarousel(FloatLayout, ChildrenFromDictsBehavior):
    """
    Carousel that constructs contents from child_dicts.

    On click, opens a modal with list of content.
    """

    carousel = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty`"""

    recycle_view_name = StringProperty()
    """:class:`~kivy.properties.StringProperty`"""

    recycle_view_data_class = StringProperty()
    """:class:`~kivy.properties.StringProperty`"""

    modal = ModalView()

    def __init__(self, **kwargs):
        super(MyCarousel, self).__init__(**kwargs)
        self.child_bindings = {
            "height": self.update_height,
            "on_press": self.open_menu,
        }
        self.on_child_dicts()

    def before_add_child(self, child):
        """Bind :meth:`set_child_width` to change of :attr:`width`."""
        self.bind(width=lambda *_: self.set_child_width(child))

    def after_add_child(self, child):
        """Call :meth:`set_child_width` after adding child."""
        self.set_child_width(child)

    def set_child_width(self, child, *_):
        """Set width of child to :attr:`width` - width of left and right-icon."""
        width = self.width - self.ids.left_icon.width - self.ids.right_icon.width
        setattr(child, "width", width)

    def update_height(self, *_):
        """Implement in sub class. Placeholder."""

    def get_modal_content(self, size_hint=(1, None)):
        """Return root widget to display on the modal."""

        def set_carousel_index(i, *_):
            self.carousel.index = i
            self.modal.dismiss()

        data_dicts = [
            {**dict, "size_hint": size_hint, "on_press": partial(set_carousel_index, i)}
            for i, dict in enumerate(self.child_dicts)
        ]
        recycle_view_cls = Factory.get(self.recycle_view_name)
        recycle_view = recycle_view_cls()
        recycle_view.child_class_name = self.recycle_view_data_class
        recycle_view.child_dicts = data_dicts
        return recycle_view

    def get_checked(self, property_name=None):
        """If ``attribute_name`` is ``None``, return currently selected widget, else return a property thereof."""
        checked_elements = [self.carousel.current_slide]
        if property_name is None:
            return checked_elements
        return [getattr(element, property_name) for element in checked_elements]

    def open_menu(self, *_):
        """Open :class:`kivy.uix.modalview.ModalView` with content given by :meth:`get_modal_content`."""
        self.modal = ModalView()
        modal_content = self.get_modal_content()
        self.modal.add_widget(modal_content)
        self.modal.open()


class ImageCarousel(MyCarousel):
    """Carousel of images."""

    def get_modal_content(self, size_hint=(1, 1)):
        """Call :meth:`MyCarousel.get_modal_content` with ``size_hint=(1,1)``."""
        return super(ImageCarousel, self).get_modal_content(size_hint=size_hint)


class CardCarousel(MyCarousel):
    """
    Carousel of :class:`TransCard`.

    To use it with different objects, change :attr:`child_class_name` and :attr:`recycle_view_data_class`.
    """

    def update_height(self, *_):
        """Update height via animation, so that Widget has height of currently displayed card."""
        if self.carousel.current_slide:
            new_height = self.carousel.current_slide.height + 24
            if self.height != new_height:
                anim = Animation(height=new_height, duration=0.5)
                anim.start(self)

    def on_child_dicts(self, *_):
        """Fix size-issue on first init."""
        super(CardCarousel, self).on_child_dicts(*_)
        if self.carousel:
            self.carousel.index = 1
            self.carousel.index = 0


# pylint: disable = W,C,R,I
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

    class _TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            return Builder.load_string(CARD_CAROUSEL_STRING)

    _TestApp().run()
