"""
Implements Different classes to display elements in a scroll view.

:class:`ScrollList` and :class:`LeftStatusIndicatorListItem`.
"""
import os
from random import choice

import toolz
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.list import ILeftBody, MDList, OneLineAvatarListItem

from custom_widgets.behaviors import (
    CallbackBehavior,
    ChildrenFromDataBehavior,
    MultiStateBehavior,
)
from paths import CUSTOM_WIDGET_DIR

Builder.unload_file(os.path.join(CUSTOM_WIDGET_DIR, "scroll_widgets.kv"))
Builder.load_file(os.path.join(CUSTOM_WIDGET_DIR, "scroll_widgets.kv"))


class LeftStatusIndicator(MultiStateBehavior, ILeftBody, AnchorLayout):
    """Contains :class:`~kivy.uix.spinner.MDSpinner` and :class:`~kivy.uix.label.MDIcon`."""

    spinner_active = BooleanProperty()
    """:class:`~kivy.properties.ObjectProperty` set to :class:`~kivy.uix.spinner.MDSpinner`."""

    icon = StringProperty()
    """:class:`~kivy.properties.ObjectProperty` set to :class:`~kivy.uix.label.MDIcon`"""

    icon_color = ListProperty()
    """:class:`~kivy.properties.ListProperty` defaults to :attr:`main.AnkiCardGenApp.theme_cls.text_color`."""

    current_state = OptionProperty(
        "queued",
        options=["loading", "queued", "waiting", "ready", "done", "error", "exported"],
    )
    """:class:`~kivy.properties.OptionProperty` with options
    ``["loading", "queued", "waiting", "ready", "done", "error", "exported"]``."""


class LeftStatusIndicatorListItem(CallbackBehavior, OneLineAvatarListItem):
    """
    Contains :class:`LeftStatusIndicator` as left element.

    Depending on :attr:`current_state`, either the spinner is active or an icon is shown.
    """

    current_state = OptionProperty(
        "queued",
        options=["loading", "queued", "waiting", "ready", "done", "error", "exported"],
    )
    """:class:`~kivy.properties.OptionProperty` with options
    ``["loading", "queued", "waiting", "ready", "done", "error", "exported"]``."""


class ScrollList(ChildrenFromDataBehavior, ScrollView):
    """
    Scrollable List whose items are constructed as instances of :attr:`item_type` from :attr:`item_dicts`.

    Automatically updates upon change of :attr:`item_dicts`.
    """

    data = ListProperty()
    """:class:`~kivy.properties.ListProperty` containing the dictionaries from which the items are constructed."""

    list = ObjectProperty(MDList())
    """
    :class:`~kivy.properties.ObjectProperty` set to :class:`~kivy.uix.MDList`.
    Contains the items.
    """


class ScrollBox(ChildrenFromDataBehavior, ScrollView):
    """
    :class:`~kivy.uix.scrollview.ScrollView` containing a :class:`~kivy.uix.boxlayout.BoxLayout`.

    Children are constructed from :attr:`child_dict` and added to the BoxLayout.
    """


class ScrollGrid(ChildrenFromDataBehavior, ScrollView):
    """
    :class:`~kivy.uix.scrollview.ScrollView` containing a :class:`~kivy.uix.gridlayout.GridLayout`.

    Children are constructed from :attr:`child_dict` and added to the BoxLayout.
    """


class RecycleViewBox(RecycleView):
    """:class:`~kivy.uix.recycleview.RecycleView` object containing a ``RecycleViewBoxLayout``."""


class RecycleList(RecycleView):
    """:class:`~kivy.uix.recycleview.RecycleView` object containing a ``RecycleViewBoxLayout``."""


Factory.register("ScrollBox", ScrollBox)
Factory.register("ScrollGrid", ScrollGrid)
Factory.register("RecycleViewBox", RecycleViewBox)
Factory.register("LeftStatusIndicatorListItem", LeftStatusIndicatorListItem)


# pylint: disable = W,C,R,I,E
if __name__ == "__main__":

    @toolz.curry
    def _schedule(sl, obj):
        if obj.current_state == "queued":
            sl.data[obj.number]["current_state"] = "loading"
            Clock.schedule_once(
                lambda dt: sl.data[obj.number].__setitem__("current_state", "ready"),
                5,
            )
        elif obj.current_state == "ready":
            sl.data[obj.number]["current_state"] = choice(["done", "error"])
        names_by_state = toolz.reduceby(
            "current_state", lambda x, y: x + [y["text"]], sl.data, list
        )
        obj.current_state = sl.data[obj.number]["current_state"]
        print(toolz.keyfilter(lambda x: x != "queued", names_by_state))

    class _TestApp(MDApp):
        def build(self):
            # sl = ScrollList(child_class_name="LeftStatusIndicatorListItem")
            # sl.data = [
            #     {"text": f"test_{i}", "callbacks": {"on_press": _schedule}}
            #     for i in range(100)
            # ]
            sl = RecycleList()  # , callback=_schedule
            sl.viewclass = "LeftStatusIndicatorListItem"
            sl.data = [
                {
                    "text": f"test_{i}",
                    "callbacks": {
                        "on_press": _schedule(sl),
                    },
                    "current_state": "queued",
                    "number": i,
                }
                for i in range(10000)
            ]
            return sl

    _TestApp().run()
