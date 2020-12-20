"""Implements various elements to get user selection."""
import os
from functools import partial

from kivy.animation import Animation
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ListProperty,
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

from custom_widgets.behaviors import (
    CheckBehavior,
    ChildrenFromDataBehavior,
    LongPressBehavior,
    ThemableColorChangeBehavior,
    TranslationOnCheckBehavior,
)
from paths import CUSTOM_WIDGET_DIR

Builder.unload_file(os.path.join(CUSTOM_WIDGET_DIR, "selection_widgets.kv"))
Builder.load_file(os.path.join(CUSTOM_WIDGET_DIR, "selection_widgets.kv"))


class SeparatorWithHeading(FloatLayout):
    r"""Two :class:`MDSeparator`\ s with a heading in between."""

    heading = StringProperty("")
    """:class:`~kivy.properties.StringProperty` with string used as heading."""


class CheckContainer(ChildrenFromDataBehavior):
    """Container for widgets with :class:`~custom_widgets.behaviors.CheckBehavior`."""

    check_one = BooleanProperty(False)
    """:class:`~kivy.properties.BooleanProperty` defaults to ``False``. If ``True`` only one child can be selected."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        return [
            getattr(element, attribute_name) for element in checked_elements if element
        ]


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
    r"""Container for :class:`MyCheckChip`\ s. Use :attr:`child_dict` to populate."""

    child_class_name = "MyCheckChip"
    draw_box = BooleanProperty(False)


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
        super().__init__(**kwargs)

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


class MyCarousel(FloatLayout, ChildrenFromDataBehavior):
    """
    Carousel that constructs contents from :attr:`data`.

    On click, opens a modal with list of content.
    """

    carousel = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty`"""

    modal_layout_name = StringProperty()
    """:class:`~kivy.properties.StringProperty`"""

    modal_data_cls_name = StringProperty()
    """:class:`~kivy.properties.StringProperty`"""

    modal = ModalView()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.child_bindings = {
            "height": self.update_height,
            "on_press": self.open_menu,
        }
        self.on_data()

    def on_data(self, *_):
        """Override :meth:`behaviors.ChildrenFromDataBehavior.on_data` with correct list of children.

        The children are in ``carousel.slides`` as opposed to ``carousel.children``.
        """
        diff = len(self.data) - len(getattr(self.carousel, "slides", []))
        if diff > 0:
            for _ in range(abs(diff)):
                self.add_child()
        else:
            for _ in range(abs(diff)):
                self.remove_child()
        for i, child_dict in enumerate(self.data):
            for key, val in child_dict.items():
                setattr(self.carousel.slides[i], key, val)

    def remove_child(self):
        """Override :meth:`behaviors.ChildrenFromDataBehavior.remove_child` with correct list of children.

        The children are in ``carousel.slides`` as opposed to ``carousel.children``.
        """
        last_slide = self.carousel.slides[-1]
        self.carousel.remove_widget(last_slide)

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
            for i, dict in enumerate(self.data)
        ]
        recycle_view_cls = Factory.get(self.modal_layout_name)
        recycle_view = recycle_view_cls()
        recycle_view.child_class_name = self.modal_data_cls_name
        recycle_view.data = data_dicts
        return recycle_view

    def get_checked(self, attribute_name=None):
        """If ``attribute_name`` is ``None``, return currently selected widget, else return a property thereof."""
        checked_elements = [self.carousel.current_slide]
        if attribute_name is None:
            return checked_elements
        return [
            getattr(element, attribute_name) for element in checked_elements if element
        ]

    def open_menu(self, *_):
        """Open :class:`kivy.uix.modalview.ModalView` with content given by :meth:`get_modal_content`."""
        self.modal = ModalView()
        modal_content = self.get_modal_content()
        self.modal.add_widget(modal_content)
        self.modal.open()


class ImageCarousel(MyCarousel):
    """Carousel of images."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.child_bindings["on_error"] = lambda *_: self.dispatch("on_error", *_)
        self.register_event_type("on_error")
        self.on_data()

    def get_modal_content(self, size_hint=(1, 1)):
        """Call :meth:`MyCarousel.get_modal_content` with ``size_hint=(1,1)``."""
        return super().get_modal_content(size_hint=size_hint)

    def on_error(self, *_):
        """Placeholder-function."""


class CardCarousel(MyCarousel):
    """
    Carousel of :class:`TransCard`.

    To use it with different objects, change :attr:`viewclass` and :attr:`modal_data_cls_name`.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        del self.child_bindings["on_press"]

    def update_height(self, *_):
        """Update height via animation, so that Widget has height of currently displayed card."""
        if self.carousel.current_slide:
            new_height = self.carousel.current_slide.height + 24
            if self.height != new_height:
                anim = Animation(height=new_height, duration=0.2)
                anim.start(self)


class RecycleCarousel(FloatLayout):
    """
    Wrapper class for a :class:`~kivy.uix.carousel.Carousel` that uses only 3 slides to update content dynamically.

    The :attr:`index` is updated according to the change of the carousel index and each time one of the slides is
    updated with data from :attr:`data`. The content of the slides is constructed as instances of :attr:`viewclass`.
    """

    carousel = ObjectProperty()
    """:class:`kivy.properties.ObjectProperty` defaults to ``None``."""
    viewclass = StringProperty("TransCard")
    """:class:`kivy.properties.StringProperty` defaults to ``"TransCard"``. Class name of the widgets that are added
    to the carousel."""
    data = ListProperty()
    """:class:`kivy.properties.ListProperty` defaults to ``None``. List of dictionaries from which the content is
    generated."""
    slide_width = NumericProperty()
    """:class:`kivy.properties.NumericProperty` defaults to ``None``. Width that the content of the slides should
    have."""
    dynamic_height = BooleanProperty(False)
    """:class:`kivy.properties.BooleanProperty` defaults to ``False``. If ``True`` updates the height of the root
    widget to the height of the object on the current slide + 24. Only possible if size_hint_y of the widget on the
    slide is not set."""
    index = NumericProperty(0)
    """:class:`kivy.properties.NumericProperty` defaults to ``0``. Current (virtual) index."""
    last_carousel_index = NumericProperty(0)
    """:class:`kivy.properties.NumericProperty` defaults to ``0``. Last index that the :attr:`carousel` had. Used to
    determine whether the user did slide right or left."""
    current_slide = ObjectProperty()
    """:class:`kivy.properties.ObjectProperty`. Reference to :attr:`carousel`.current_slide."""

    modal_layout_name = StringProperty()
    """:class:`kivy.properties.StringProperty` defaults to ``None``. Class name for root widget of :attr:`modal`."""
    modal_data_cls_name = StringProperty()
    """:class:`kivy.properties.StringProperty` defaults to ``None``. Class name for children of :attr:`modal`."""
    modal = ObjectProperty(ModalView())
    """:class:`kivy.properties.ObjectProperty` defaults to ``ModalView()``."""
    default_modal_size_hint = ListProperty([1, None])

    def update_height(self, *_):
        """Update height via animation, so that Widget has height of currently displayed card."""
        if self.dynamic_height:
            new_height = self.carousel.current_slide.height + 24
            if self.height != new_height:
                anim = Animation(height=new_height, duration=0.3)
                anim.start(self)

    def setup_modal(self):
        """Return root widget to display on the modal."""
        self.modal = ModalView()
        modal_root_cls = Factory.get(self.modal_layout_name)
        modal_root = modal_root_cls()
        self.modal.add_widget(modal_root)

    def _modal_child_callback(self, i, *_):
        self.set_index(i)
        self.modal.dismiss()

    def update_modal_content(self):
        """Update content of modal."""
        data_dicts = [
            {
                **dict,
                "size_hint": self.default_modal_size_hint,
                "on_press": partial(self._modal_child_callback, i),
            }
            for i, dict in enumerate(self.data)
        ]
        self.modal.children[0].child_class_name = self.modal_data_cls_name
        self.modal.children[0].data = data_dicts

    def get_checked(self, attribute_name=None):
        """If ``attribute_name`` is ``None``, return currently selected widget, else return a property thereof."""
        checked_elements = [self.carousel.current_slide]
        if attribute_name is None:
            return checked_elements
        return [
            getattr(element, attribute_name) for element in checked_elements if element
        ]

    def open_menu(self, *_):
        """Open :class:`kivy.uix.modalview.ModalView` with content given by :meth:`setup_modal`."""
        if not self.modal.children:
            self.setup_modal()
        self.update_modal_content()
        self.modal.open()

    def on_data(self, *_):
        """Set up :attr:`carousel` by initializing 3 widgets, adding them and binding some Properties."""
        self.carousel.clear_widgets()
        if len(self.data) >= 3:
            for i in [0, 1, -1]:
                widget = Factory.get(self.viewclass)(**self.data[i])
                self.carousel.add_widget(widget)
                self.bind(slide_width=widget.setter("width"))
                widget.bind(on_press=self.open_menu)
                widget.width = self.slide_width
            self.carousel.register_event_type("on_index")
            self.carousel.bind(index=self.update_index)
            self.carousel.bind(current_slide=self.update_height)
            self.carousel.current_slide.bind(height=self.update_height)
        print("RecylceCarousel needs at least 3 elements to be displayed correctly.")

    def update_index(self, _, carousel_index):
        """Change :attr:`index` according to change in ``carousel_index`` and update one of the three slides."""
        diff = carousel_index - self.last_carousel_index
        diff = -1 if diff == 2 else 1 if diff == -2 else diff
        self.last_carousel_index = carousel_index
        self.index = (self.index + diff) % len(self.data)
        self.update_slide(carousel_index + diff, self.index + diff)

    def update_slide(self, carousel_index, index):
        """
        Update slide with index ``carousel_index`` by content from :attr:`data` [index].

        Modulo function applied to indices guarantees values to be in the correct range.
        """
        carousel_index %= 3
        index %= len(self.data)
        for name, val in self.data[index].items():
            setattr(self.carousel.slides[carousel_index], name, val)

    def set_index(self, index):
        """Set :attr:`index` to ``index`` and updates carousel accordingly."""
        self.index = index
        self.update_height()
        for i in [0, 1, -1]:
            self.update_slide((self.last_carousel_index + i) % 3, self.index + i)


# pylint: disable = W,C,R,I
if __name__ == "__main__":
    CARD_CAROUSEL_STRING = (
        "CardCarousel:\n"
        '    data: [{"text_orig":str(i)*50*i,"text_trans":"Trans"} for i in range(10)]'
    )

    RECYCLE_CAROUSEL_STRING = (
        "RecycleCardCarousel:\n"  # some comment
        '    data: [{"text_orig":str(i)*50*i,"text_trans":"Trans"} for i in range(10)]'
    )

    IMAGE_CAROUSEL_STRING = (
        "ImageCarousel:\n"
        '    data: [{"source":"../assets/AnkiCardGen.png"} for _ in range(5)]'
    )

    class _TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Light"  # "Purple", "Red"
            return Builder.load_string(RECYCLE_CAROUSEL_STRING)

    _TestApp().run()
