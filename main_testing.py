from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.tab import MDTabsBase, MDTabs

from anki_scripts.new_main import Query


class Tab(ScrollView, MDTabsBase):
    pass


class MyTabs(MDTabs):
    def __init__(self, **kwargs):
        super(MyTabs, self).__init__(**kwargs)


class MyApp(MDApp):
    word = ObjectProperty(Query())
    search_term = StringProperty()

    def build(self):
        return Builder.load_string("""
<ScrollView>:
    do_scroll_x:False
MyTabs:
    Tab:
        do_scroll_x: False
        do_scroll_y: True
        size_hint: 1,1
        WordProperties:
            size_hint:1,None
            height: self.minimum_height
            MDFlatButton:
                text: "test"
                on_press: root.ids.carousel.ignore_perpendicular_swipes = not root.ids.carousel.ignore_perpendicular_swipes
    Tab:
        do_scroll_x: False
        do_scroll_y: True
        size_hint: 1,1
        WordProperties:
            size_hint:1,None
            height: self.minimum_height
    Tab:
        do_scroll_x: False
        do_scroll_y: True
        size_hint: 1,1
        WordProperties:
            size_hint:1,None
            height: self.minimum_height
    Tab:
        do_scroll_x: False
        do_scroll_y: True
        size_hint: 1,1
        WordProperties:
            size_hint:1,None
            height: self.minimum_height

                """)


MyApp().run()
