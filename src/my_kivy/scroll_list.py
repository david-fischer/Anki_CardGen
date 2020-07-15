"""
Implements :class:`ScrollList` and :class:`LeftStatusIndicatorListItem`.
"""

from functools import partial
from threading import Thread
from time import sleep

from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty, OptionProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.list import ILeftBody, MDList, OneLineAvatarListItem, OneLineListItem

Builder.load_string(
    """
<LeftStatusIndicator>:
    spinner: spinner
    active: False
    icon: ""

    MDIcon:
        id: _icon
        icon: root.icon
        color: (0,1,0 ,1 )
        size_hint: 1,1
        font_size: 30
        texture_size: self.size

    MDSpinner:
        id: spinner
        active: root.active
        size_hint: 0.7,0.7
        opacity: float(root.active)

<LeftStatusIndicatorListItem>:
    loading_state: "queued"
    active: self.loading_state=="loading"
    icon: "check-circle" if self.loading_state=="ready" else ""


    LeftStatusIndicator:
        active: root.active
        icon: root.icon


<ScrollList>:
    list: md_list
    ScrollView:
        MDList:
            id: md_list
    """
)


class ScrollList(ScrollView):
    """
    Scrollable List whose items are constructed as instances of :attr:`item_type` from :attr:`item_dicts`.

    Automatically updates upon change of :attr:`item_dicts`.
    """

    item_type = ObjectProperty(OneLineListItem)
    """:class:`~kivy.properties.ObjectProperty` constructor for items."""

    item_dicts = ListProperty()
    """:class:`~kivy.properties.ListProperty` containing the dictionaries from which the items are constructed."""

    items = ListProperty()
    """:class:`~kivy.properties.ListProperty` containing the constructed items."""

    list = ObjectProperty(MDList())
    """
    :class:`~kivy.properties.ObjectProperty` set to :class:`~kivy.uix.MDList`.
    Contains the items.
    """

    callback = ObjectProperty(lambda x: print(x.text))
    """:class:`~kivy.properties.ObjectProperty`"""

    def __init__(self, **kwargs):
        super(ScrollList, self).__init__(**kwargs)
        self.on_item_dicts()

    @mainthread
    def on_item_dicts(self, *_):
        """
        Construct items from :attr:`item_dicts` using :attr:`item_type`.
        """
        items = [
            self.item_type(**item_dict, on_press=self.callback)
            for item_dict in self.item_dicts
        ]
        self.list.clear_widgets()
        for item in items:
            item.root = self
            self.list.add_widget(item)


class LeftStatusIndicator(ILeftBody, AnchorLayout):
    """
    Contains :class:`~kivy.uix.spinner.MDSpinner` and :class:`~kivy.uix.label.MDIcon`.
    """

    spinner = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty` set to :class:`~kivy.uix.spinner.MDSpinner`."""

    icon = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty` set to :class:`~kivy.uix.label.MDIcon`"""


class LeftStatusIndicatorListItem(OneLineAvatarListItem):
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


def _schedule(obj):
    if obj.loading_state == "queued":
        obj.loading_state = "loading"
        sleep(10)
        Clock.schedule_once(lambda dt: setattr(obj, "loading_state", "ready"), 5)


# pylint: disable = W,C,R,I
if __name__ == "__main__":

    class TestApp(MDApp):
        def build(self):
            return ScrollList(
                item_type=LeftStatusIndicatorListItem,
                item_dicts=[{"text": "test"}] * 25,
                callback=lambda obj: Thread(target=partial(_schedule, obj)).start(),
            )

    TestApp().run()
