from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, ListProperty, Property
from kivymd.uix.imagelist import Tile

class CheckTile(Tile):
    source=StringProperty()
    alternative_source=StringProperty("assets/camera.png")
    color=ListProperty([0,0,0,0])
    checked=BooleanProperty(False)
    checked_op=Property(1)
    unchecked_op=Property(0.7)
    opacity = Property(0.7)


class MyApp(MDApp):
    def build(self):
        return Builder.load_file("picture_picker.kv")


if __name__ == "__main__":
    MyApp().run()
