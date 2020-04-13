from kivy.app import runTouchApp
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


class TestBox(BoxLayout):
    def on_touch_move(self, touch):
        print(touch.dpos)


class MyButton(Button):
    def on_touch_up(self, touch):
        pass


root = Builder.load_string(
    """
ScrollView:
    do_scroll_x: False
    do_scroll_y: True
    
    MyCardChooser:
        MyCard:
            text:
                'really some amazing text\\n' * 100"""
)

runTouchApp(root)
