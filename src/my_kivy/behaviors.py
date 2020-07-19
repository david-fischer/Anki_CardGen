"""
Provides various mixin-classes for kivy widgets.

.. :autosummary:
"""
from functools import partial
from threading import Thread

from kivy import clock
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.properties import (
    DictProperty,
    ListProperty,
    ObjectProperty,
    Property,
    StringProperty,
)


class CallbackBehavior(EventDispatcher):
    """
    Mixin Class to implement a number of callbacks.

    Usefull e.g. in combination with :class:`~kivy.uix.recycleview.RecycleView`.
    There, the content is generated dynamically from a dictionary such that this class can be used to bind multiple
    callbacks to different events of the widgets.

    Warnings:
        Callbacks are not unbound by :meth:`on_callbacks`.
        Does this pose a problem?
    """

    callbacks = DictProperty()
    """:class:`~kivy.propterty.DictProperty` of the form {"on_event": callback_fn}.
    callback_fn(self) -> Any
    """

    def on_callbacks(self, *_):
        """Binds the callbacks to the specified events on definition."""
        for event, callback_fn in self.callbacks.items():
            self.bind(**{event: partial(self.callback_wrapper, callback_fn)})

    def callback_wrapper(self, callback, *_):
        """Wrapper to call callback in new thread."""
        thread = Thread(target=partial(callback, self))
        thread.start()


class LongPressBehavior(EventDispatcher):
    """
    Dispatches "on_long_press" if pressed for longer than :attr:`long_press_time`.
    """

    long_press_time = Factory.NumericProperty(1)
    """:class:`~kivy.properties.NumericProperty`"""

    def __init__(self, **kwargs):
        super(LongPressBehavior, self).__init__(**kwargs)
        self._clockev = None
        self.register_event_type("on_long_press")

    def on_state(self, instance, value):
        """Dispatches ``on_long_press`` if the :attr:`state` stays down for longer than :attr:`long_press_time`."""
        try:
            super(LongPressBehavior, self).on_state(instance, value)
        except AttributeError:
            pass
        if value == "down":
            lpt = self.long_press_time
            self._clockev = Clock.schedule_once(self._do_long_press, lpt)
        else:
            self._clockev.cancel()

    def _do_long_press(self, _):
        """Helper function."""
        self.dispatch("on_long_press")

    def on_long_press(self, *largs):
        """Placeholder."""


class MultiStateBehaviour:
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
        super(MultiStateBehaviour, self).__init__(**kwargs)
        clock.Clock.schedule_once(self.__post_init__)

    def on_current_state(self, *_):
        """
        Changes widgets properties based on new :attr:`current_state`.

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
        self.on_current_state()


class CheckBehavior(MultiStateBehaviour):
    """Two-State-Behavior with states ``True`` and ``False``."""

    def __init__(self, **kwargs):
        self.current_state = False
        self.state_dicts = (
            {True: {}, False: {}} if self.state_dicts is None else self.state_dicts
        )
        super(CheckBehavior, self).__init__(**kwargs)


class ChildrenFromDictsBehavior:
    """
    Generates widgets dynamically from :attr:`child_dicts` and adds them to :attr:`root_for_children`.

    Bindings can be applied and other functions executed by the definition of :meth:`before_add_child` and
    :meth:`after_add_child`.
    """

    child_dicts = ListProperty([])
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
        super(ChildrenFromDictsBehavior, self).__init__(**kwargs)
        if self.root_for_children is None:
            self.root_for_children = self
        self.on_child_dicts()

    def on_child_dicts(self, *_):
        """Constructs children on change of :attr:`child_dicts`."""
        self.root_for_children.clear_widgets()
        for child_dict in self.child_dicts:
            child_cls = Factory.get(self.child_class_name)
            new_child = child_cls(**child_dict)
            if self.child_bindings:
                new_child.bind(**self.child_bindings)
            self.before_add_child(new_child)
            self.root_for_children.add_widget(new_child)
            self.after_add_child(new_child)

    def before_add_child(self, child):
        """Function to be executed before child is added to :attr:`parent_widget`."""

    def after_add_child(self, child):
        """Function to be executed before child is added to :attr:`parent_widget`."""


class TranslationOnCheckBehavior:
    """
    Switches :attr:`text` between :attr:`text_orig` and :attr:`text_trans` depending on :attr:`current_state`.

    Needs inheritance from :class:`CheckBehavior`.
    """

    text_orig = StringProperty("orig")
    """:class:`~kivy.properties.StringProperty`. Original Text."""

    text_trans = StringProperty("trans")
    """:class:`~kivy.properties.StringProperty`. Translated Text."""

    def __post_init__(self, *_):
        self.state_dicts[True]["text"] = self.text_orig
        self.state_dicts[False]["text"] = self.text_trans
        super(TranslationOnCheckBehavior, self).__post_init__(*_)


class ThemableColorChangeBehavior:
    """
    Changes :attr:`bg_color` :attr:`text_color` based on :attr:`current_state`.

    Needs inheritance from :class:`CheckBehavior`.
    """

    text_color = ListProperty([0, 0, 0, 1])
    """:class:`~kivy.properties.ListProperty`. Text color in rgba."""

    bg_color = ListProperty([1, 1, 1, 1])
    """:class:`~kivy.properties.ListProperty`. Background color in rgba."""

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
