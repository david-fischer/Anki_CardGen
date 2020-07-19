"""
Implements Different classes to display elements in a scroll view.

:class:`ScrollList` and :class:`LeftStatusIndicatorListItem`.
"""
import os
from functools import partial
from threading import Thread
from time import sleep

from kivy.clock import Clock, mainthread
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import (
    DictProperty,
    ListProperty,
    ObjectProperty,
    OptionProperty,
)
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.list import ILeftBody, MDList, OneLineAvatarListItem

from my_kivy.mychooser import ChildrenFromDictsBehavior

try:
    Builder.load_file("my_kivy/scroll_list.kv")
except FileNotFoundError:
    this_directory = os.path.dirname(__file__)
    Builder.load_file(os.path.join(this_directory, "scroll_list.kv"))


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


class LeftStatusIndicator(ILeftBody, AnchorLayout):
    """
    Contains :class:`~kivy.uix.spinner.MDSpinner` and :class:`~kivy.uix.label.MDIcon`.
    """

    spinner = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty` set to :class:`~kivy.uix.spinner.MDSpinner`."""

    icon = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty` set to :class:`~kivy.uix.label.MDIcon`"""


class LeftStatusIndicatorListItem(CallbackBehavior, OneLineAvatarListItem):
    """
    Contains :class:`LeftStatusIndicator` as left element.

    Depending on :attr:`loading_state`, either the spinner is active or an icon is shown.
    """

    loading_state = OptionProperty("queued", options=["loading", "queued", "ready"])
    """:class:`~kivy.properties.OptionProperty` with options ``["loading", "queued", "ready"]``."""

    spinner = ObjectProperty()
    """
    :class:`~kivy.properties.ObjectProperty` reference to instance of :class:`~kivy.uix.spinner.MDSpinner` of
    :class:`LeftStatusIndicator`.
    """


Factory.register("LeftStatusIndicatorListItem", LeftStatusIndicatorListItem)


class ScrollList(ChildrenFromDictsBehavior, ScrollView):
    """
    Scrollable List whose items are constructed as instances of :attr:`item_type` from :attr:`item_dicts`.

    Automatically updates upon change of :attr:`item_dicts`.
    """

    # item_type = ObjectProperty(OneLineListItem)
    # """:class:`~kivy.properties.ObjectProperty` constructor for items."""

    child_dicts = ListProperty()
    """:class:`~kivy.properties.ListProperty` containing the dictionaries from which the items are constructed."""

    list = ObjectProperty(MDList())
    """
    :class:`~kivy.properties.ObjectProperty` set to :class:`~kivy.uix.MDList`.
    Contains the items.
    """

    callback = ObjectProperty(lambda self, obj: print(obj.text))

    def __init__(self, **kwargs):
        super(ScrollList, self).__init__(**kwargs)
        self.child_bindings["on_press"] = self.callback_wrapper

    # TODO: callback_wrapper correct? Check if this is the desired behavior.
    def callback_wrapper(self, obj, *_):
        """Wrapper to execute callback in new thread."""
        thread = Thread(target=partial(self.callback, obj))
        thread.start()

    @mainthread
    def on_child_dicts(self, *_):
        """mainthread decorator ensures that changes are displayed correctly."""
        super(ScrollList, self).on_child_dicts(*_)


def _schedule(obj):
    if obj.loading_state == "queued":
        obj.loading_state = "loading"
        sleep(5)
        Clock.schedule_once(lambda dt: setattr(obj, "loading_state", "ready"), 5)


class RecycleList(RecycleView):
    """
    :class:`~kivy.uix.recycleview.RecycleView` object containing a ``RecycleViewBoxLayout`` and some formatting
    instructions.
    """


# pylint: disable = W,C,R,I
if __name__ == "__main__":

    class TestApp(MDApp):
        def build(self):
            sl = RecycleList()  # , callback=_schedule
            sl.viewclass = "LeftStatusIndicatorListItem"
            sl.data = [
                {
                    "text": f"test_{i}",
                    "callback": _schedule,
                    "callback_binding": "on_press",
                    "loading_state": "queued",
                }
                for i in range(10000)
            ]
            return sl

    TestApp().run()
