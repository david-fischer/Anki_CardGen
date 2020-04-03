from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.tab import MDTabs, MDTabsBase


class Tab(FloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    id = StringProperty("")
    text = StringProperty("")
    icon = StringProperty("")


class MyTabs(MDTabs):
    pass


Builder.load_file("tabs.kv")


class TestApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"  # "Purple", "Red"
        self.theme_cls.theme_style = "Light"  # "Purple", "Red"
        return Builder.load_string("""
BoxLayout:
    orientation: "vertical"
    MyTabs:
        id: my_tabs
""")

if __name__ == "__main__":
    TestApp().run()
