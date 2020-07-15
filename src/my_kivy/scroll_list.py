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
    item_type = ObjectProperty(OneLineListItem)
    """:class:`~kivy.properties.ObjectProperty`"""

    item_dicts = ListProperty()
    """:class:`~kivy.properties.ListProperty`"""

    items = ListProperty()
    """:class:`~kivy.properties.ListProperty`"""

    list = ObjectProperty(MDList())
    """:class:`~kivy.properties.ObjectProperty`"""

    callback = ObjectProperty(lambda x: print(x.text))
    """:class:`~kivy.properties.ObjectProperty`"""

    def __init__(self, **kwargs):
        super(ScrollList, self).__init__(**kwargs)
        self.on_item_dicts()

    @mainthread
    def on_item_dicts(self, *_):
        items = [
            self.item_type(**item_dict, on_press=self.callback)
            for item_dict in self.item_dicts
        ]
        self.list.clear_widgets()
        for item in items:
            item.root = self
            self.list.add_widget(item)


class LeftStatusIndicator(ILeftBody, AnchorLayout):
    spinner = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty`"""

    icon = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty`"""


class LeftStatusIndicatorListItem(OneLineAvatarListItem):
    loading_state = OptionProperty("queued", options=["loading", "queued", "ready"])
    """:class:`~kivy.properties.OptionProperty`"""

    spinner = ObjectProperty()
    """:class:`~kivy.properties.ObjectProperty`"""


def schedule(obj):
    if obj.loading_state == "queued":
        obj.loading_state = "loading"
        sleep(10)
        Clock.schedule_once(lambda dt: setattr(obj, "loading_state", "ready"), 5)


if __name__ == "__main__":

    class TestApp(MDApp):
        def build(self):
            return ScrollList(
                item_type=LeftStatusIndicatorListItem,
                item_dicts=[{"text": "test"}] * 25,
                callback=lambda obj: Thread(target=partial(schedule, obj)).start(),
            )

    TestApp().run()