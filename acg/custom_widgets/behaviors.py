"""Provides various mixin-classes for kivy widgets."""

from functools import partial
from threading import Thread

import toolz
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.properties import (
    AliasProperty,
    DictProperty,
    ListProperty,
    ObjectProperty,
    Property,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivymd.theming import ThemableBehavior


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


class RightClickBehavior(Widget):
    """Mixin class that provides ``on_special_click`` event. Currently this is triggered by right-click."""

    # TODO: extend to long-press for mobile
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_special_click")

    def on_touch_down(self, touch):
        """Dispatch ``"on_special_click"``-event if right-click is detected on widget.

        Otherwise call normal touch event.
        """
        if touch.button == "right":
            if self.collide_point(*touch.pos):
                self.dispatch("on_special_click")
                return True
            return False
        return super().on_touch_down(touch)

    def on_special_click(self, *_):
        """Placeholder-function."""


class MultiStateBehavior(Widget):
    """
    Changes properties of widget based on :attr:`current_state` and the corresponding entry in :attr:`state_dict`.

    The properties in :attr:`animated_properties` change via animation.
    """

    current_state = Property(None)
    """:class:`~kivy.properties.Property` current state of the widget."""
    default_state = Property(None)
    """:class:`~kivy.properties.Property` current state of the widget."""

    state_dicts = DictProperty({})
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

    animation_kwargs = DictProperty({"duration": 0.5, "t": "out_circ"})

    def _get_current_property(self):
        defaults = (
            self.state_dicts[self.default_state]
            if self.default_state in self.state_dicts
            else {}
        )
        current = (
            self.state_dicts[self.current_state]
            if self.current_state in self.state_dicts
            else {}
        )
        return {**defaults, **current}

    current_properties = AliasProperty(
        _get_current_property,
        bind=["state_dicts", "current_state", "default_state"],
    )

    def _get_properties_to_update(self):
        props = self.properties()
        props = {
            key
            for key, val in self.current_properties.items()
            if key in props and val != getattr(self, key)
        }
        animated = set(self.animated_properties)
        return props & animated, props - animated

    def _animated_update(self, keys):
        if keys:
            animation = Animation(
                **{key: self.current_properties[key] for key in keys},
                **self.animation_kwargs
            )
            animation.start(self)

    def update_properties(self, *_):
        """Update properties if they differ from the corresponding entry in :attr:`current_properties`."""
        animated, not_animated = self._get_properties_to_update()
        for key in not_animated:
            setattr(self, key, self.current_properties[key])
        self._animated_update(animated)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(current_properties=self.update_properties)
        Clock.schedule_once(self.update_properties)


class CheckBehavior(MultiStateBehavior):
    """Two-State-Behavior with states ``True`` and ``False``."""

    def __init__(self, **kwargs):
        kwargs.setdefault("state_dicts", {False: {}, True: {}})
        kwargs.setdefault("current_state", False)
        kwargs.setdefault("default_state", False)
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

    def get_child(self, name):
        """Return child with name ``name``."""
        return toolz.first(c for c in self.root_for_children.children if c.name == name)

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
        if self.root_for_children:
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

    def on_text_trans(self, *_):
        """Update :attr:`state_dict` with new :attr:`text_trans`."""
        self.state_dicts[False] |= {"text": self.text_trans}

    def on_text_orig(self, *_):
        """Update :attr:`state_dict` with new :attr:`text_orig`."""
        self.state_dicts[True] |= {"text": self.text_orig}


class ThemableColorChangeBehavior(ThemableBehavior, CheckBehavior):
    """Changes :attr:`bg_color` :attr:`text_color` based on :attr:`current_state`."""

    text_color = ListProperty([0, 0, 0, 1])
    """:class:`~kivy.properties.ListProperty`. Text color in rgba."""

    bg_color = ListProperty([1, 1, 1, 1])
    """:class:`~kivy.properties.ListProperty`. Background color in rgba."""

    animated_properties = ["bg_color", "text_color"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.bind(
            theme_style=self.set_colors, primary_palette=self.set_colors
        )
        self.set_colors()

    def set_colors(self, *_):
        """Update :attr:`state_dicts` with colors from theme."""
        self.state_dicts[True].update(
            bg_color=self.theme_cls.primary_color, text_color=[1, 1, 1, 1]
        )
        self.state_dicts[False].update(
            bg_color=self.theme_cls.bg_darkest
            if self.theme_cls.theme_style == "Light"
            else self.theme_cls.bg_light,
            text_color=self.theme_cls.secondary_text_color,
        )
        self.update_properties()
