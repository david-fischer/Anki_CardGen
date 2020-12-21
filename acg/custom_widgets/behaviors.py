"""Provides various mixin-classes for kivy widgets."""
from functools import partial
from threading import Thread

from kivy import clock
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    ListProperty,
    ObjectProperty,
    Property,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior


class CallbackBehavior(EventDispatcher):
    """
    Mixin Class to implement a number of callbacks.

    Useful e.g. in combination with :class:`~kivy.uix.recycleview.RecycleView`.
    There, the content is generated dynamically from a dictionary such that this class can be used to bind multiple
    callbacks to different events of the widgets.

    Warnings:
        Callbacks are not unbound by :meth:`on_callbacks`.
        Does this pose a problem?
    """

    callbacks = DictProperty()
    """:class:`~kivy.property.DictProperty` of the form {"on_event": callback_fn}.
    callback_fn(self) -> Any
    """

    def on_callbacks(self, *_):
        """Binds the callbacks to the specified events on definition."""
        for event, callback_fn in self.callbacks.items():
            self.bind(**{event: partial(self.callback_wrapper, callback_fn)})

    def callback_wrapper(self, callback, *_):
        """Call ``callback`` with first argument as ``self`` in new thread."""
        thread = Thread(target=partial(callback, self))
        thread.start()


class LongPressBehavior(ButtonBehavior):
    """Dispatches "on_long_press" if pressed for longer than :attr:`long_press_time` else "on_short_press"."""

    long_press_time = Factory.NumericProperty(0.4)
    """:class:`~kivy.properties.NumericProperty`"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._clockev = None
        self.register_event_type("on_long_press")
        self.register_event_type("on_short_press")

    def on_state(self, instance, value):
        """Dispatches ``on_long_press`` if the :attr:`state` stays down for longer than :attr:`long_press_time`."""
        try:
            super().on_state(instance, value)
        except AttributeError:
            pass
        if value == "down":
            self._clockev = Clock.schedule_once(
                self._do_long_press, self.long_press_time
            )
        else:
            if self._clockev in Clock.get_events():
                self._clockev.cancel()
                self.dispatch("on_short_press")

    def _do_long_press(self, _):
        """Dispatch ``"on_long_press"`` event."""
        self.dispatch("on_long_press")

    def on_long_press(self, *largs):
        """Implement in sub class. Placeholder."""

    def on_short_press(self, *largs):
        """Implement in sub class. Placeholder."""


class MultiStateBehavior:
    """
    Changes properties of widget based on :attr:`current_state` and the corresponding entry in :attr:`state_dict`.

    The properties in :attr:`animated_properties` change via animation.
    """

    current_state = Property(None)
    """:class:`~kivy.properties.Property` current state of the widget."""

    state_dicts = DictProperty(None)
    """
    :class:`~kivy.properties.DictProperty`. E.g.,
    ::

        state_dicts = {
                state_1 : {"some_property": some_value, ...},
                ...
            }
    """

    animated_properties = ListProperty()
    """:class:`~kivy.properties.ListProperty` containing the list of property-names that get changed via animation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        clock.Clock.schedule_once(self.__post_init__)

    def on_current_state(self, *_):
        """
        Change widgets properties based on new :attr:`current_state`.

        The properties whose names are in :attr:`animated_properties` are changed via animation.
        """
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
        """Do init after kv-file is applied."""
        self.on_current_state()


class CheckBehavior(MultiStateBehavior):
    """Two-State-Behavior with states ``True`` and ``False``."""

    current_state = BooleanProperty(False)
    """:class:`~kivy.properties.BooleanProperty` defaults to ``False``. State of widget."""

    def __init__(self, **kwargs):
        self.state_dicts = (
            {True: {}, False: {}} if self.state_dicts is None else self.state_dicts
        )
        """: : :class:`~kivy.properties.DictProperty`, defaults to ``{False:{}, True:{}}`` ."""
        super().__init__(**kwargs)


class ChildrenFromDataBehavior:
    """
    Generates widgets dynamically from :attr:`data` and adds them to :attr:`root_for_children`.

    Bindings can be applied and other functions executed by the definition of :meth:`before_add_child` and
    :meth:`after_add_child`.
    """

    data = ListProperty([])
    """
    :class:`~kivy.properties.ListProperty` containing the dictionaries from which the child-widgets are
    constructed.
    """

    child_class_name = StringProperty([])
    """:class:`~kivy.properties.StringProperty` class name for children. Needs to be available via
    :meth:`~kivy.factory.Factory.get`."""

    root_for_children = ObjectProperty()
    """
    :class:`~kivy.properties.ObjectProperty` the widget, where the children should be added to
    Defaults to self.
    """

    child_bindings = DictProperty()
    """:class:`~kivy.properties.DictProperty` of the form {"on_event": binding_fn}."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.root_for_children is None:
            self.root_for_children = self
        self.on_data()

    def add_child(self, child_dict=None):
        """Add one child-widget."""
        child_cls = Factory.get(self.child_class_name)
        child_dict = child_dict or {}
        new_child = child_cls(**child_dict)
        if self.child_bindings:
            new_child.bind(**self.child_bindings)
        self.before_add_child(new_child)
        self.root_for_children.add_widget(new_child)
        self.after_add_child(new_child)

    def remove_child(self):
        """Remove one child-widget."""
        last_child = self.root_for_children.children[-1]
        self.root_for_children.remove_widget(last_child)

    def update_num_children(self):
        """Add/remove children until correct number is reached."""
        diff = len(self.data) - len(self.root_for_children.children)
        for _ in range(abs(diff)):
            if diff > 0:
                self.add_child()
            else:
                self.remove_child()

    def on_data(self, *_):
        """Update children on change of :attr:`data`."""
        self.update_num_children()
        for i, child_dict in enumerate(self.data):
            for key, val in child_dict.items():
                setattr(self.root_for_children.children[-i - 1], key, val)

    def before_add_child(self, child):
        """Do something before child is added to :attr:`parent_widget`. Placeholder."""

    def after_add_child(self, child):
        """Do something after child is added to :attr:`parent_widget`. Placeholder."""


class TranslationOnCheckBehavior(CheckBehavior):
    """Switches :attr:`text` between :attr:`text_orig` and :attr:`text_trans` depending on :attr:`current_state`."""

    text_orig = StringProperty("orig")
    """:class:`~kivy.properties.StringProperty`. Original Text."""

    text_trans = StringProperty("trans")
    """:class:`~kivy.properties.StringProperty`. Translated Text."""

    def __post_init__(self, *_):
        """Initialize widget after kv-file is loaded."""
        self.state_dicts[True]["text"] = self.text_orig
        self.state_dicts[False]["text"] = self.text_trans
        super().__post_init__(*_)


class ThemableColorChangeBehavior(CheckBehavior):
    """Changes :attr:`bg_color` :attr:`text_color` based on :attr:`current_state`."""

    text_color = ListProperty([0, 0, 0, 1])
    """:class:`~kivy.properties.ListProperty`. Text color in rgba."""

    bg_color = ListProperty([1, 1, 1, 1])
    """:class:`~kivy.properties.ListProperty`. Background color in rgba."""

    animated_properties = ["bg_color", "text_color"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        super().__post_init__()
